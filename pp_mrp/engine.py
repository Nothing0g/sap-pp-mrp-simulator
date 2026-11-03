"""Small, explainable MRP simulation over a SQLite SAP-style learning schema."""
from __future__ import annotations

import csv
import math
import sqlite3
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


class PlanningError(ValueError):
    """Raised when master data or demand cannot support an explainable plan."""


@dataclass(frozen=True)
class PlannedOrder:
    planned_order_id: str
    material_id: str
    description: str
    plant: str
    order_category: str
    planned_qty: float
    base_uom: str
    start_date: str
    finish_date: str
    lead_time_days: int


@dataclass(frozen=True)
class MaterialNetting:
    material_id: str
    gross_requirement: float
    opening_stock: float
    safety_stock: float
    planned_receipts: float
    closing_projected_stock: float


@dataclass(frozen=True)
class PlanningResult:
    orders: tuple[PlannedOrder, ...]
    netting: tuple[MaterialNetting, ...]


def _iso_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise PlanningError(f"{label} must be an ISO date (YYYY-MM-DD): {value!r}") from exc


def _topological_material_order(connection: sqlite3.Connection) -> list[str]:
    materials = {row[0] for row in connection.execute("SELECT material_id FROM MARA")}
    children: dict[str, set[str]] = defaultdict(set)
    indegree = {material: 0 for material in materials}
    for row in connection.execute(
        "SELECT DISTINCT parent_material, component_material "
        "FROM STKO JOIN STPO USING (bom_id)"
    ):
        parent, component = row
        if parent not in materials or component not in materials:
            raise PlanningError(f"BOM references an unknown material: {parent} -> {component}")
        if component not in children[parent]:
            children[parent].add(component)
            indegree[component] += 1

    ready = deque(sorted(material for material, degree in indegree.items() if degree == 0))
    result: list[str] = []
    while ready:
        material = ready.popleft()
        result.append(material)
        for component in sorted(children[material]):
            indegree[component] -= 1
            if indegree[component] == 0:
                ready.append(component)
    if len(result) != len(materials):
        cyclic = sorted(material for material, degree in indegree.items() if degree > 0)
        raise PlanningError("BOM cycle detected; planning stopped for materials: " + ", ".join(cyclic))
    return result


def _material_master(connection: sqlite3.Connection, material_id: str, plant: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT A.material_id, A.description, A.base_uom, C.procurement_type, "
        "C.planned_lead_time_days, C.lot_size, C.safety_stock "
        "FROM MARA A JOIN MARC C USING (material_id) "
        "WHERE A.material_id = ? AND C.plant = ?",
        (material_id, plant),
    ).fetchone()
    if row is None:
        raise PlanningError(f"No material/plant master data for {material_id} at plant {plant}")
    return row


def _opening_stock(connection: sqlite3.Connection, material_id: str, plant: str) -> float:
    row = connection.execute(
        "SELECT COALESCE(SUM(unrestricted_qty), 0) FROM MARD "
        "WHERE material_id = ? AND plant = ?",
        (material_id, plant),
    ).fetchone()
    return float(row[0])


def _routing_lead_time(
    connection: sqlite3.Connection,
    material_id: str,
    plant: str,
    planned_qty: float,
    finish_date: date,
    fallback_days: int,
) -> int:
    """Estimate calendar-day offset using sequential routing operations and work-center minutes/day."""
    route = connection.execute(
        "SELECT routing_id FROM PLKO WHERE material_id = ? AND plant = ? "
        "AND valid_from <= ? AND valid_to >= ? ORDER BY routing_id LIMIT 1",
        (material_id, plant, finish_date.isoformat(), finish_date.isoformat()),
    ).fetchone()
    if route is None:
        return fallback_days

    rows = connection.execute(
        "SELECT O.setup_minutes, O.run_minutes_per_unit, W.available_minutes_per_day "
        "FROM PLPO O JOIN CRHD W USING (work_center) WHERE O.routing_id = ? "
        "ORDER BY O.operation_no",
        (route[0],),
    ).fetchall()
    if not rows:
        return fallback_days

    routing_days = 0
    for operation in rows:
        total_minutes = float(operation[0]) + float(operation[1]) * planned_qty
        routing_days += math.ceil(total_minutes / int(operation[2]))
    return max(fallback_days, routing_days)


def _active_bom(
    connection: sqlite3.Connection, material_id: str, effective_date: date
) -> tuple[str, list[sqlite3.Row]] | None:
    header = connection.execute(
        "SELECT bom_id FROM STKO WHERE parent_material = ? AND valid_from <= ? AND valid_to >= ? "
        "ORDER BY alternative, bom_id LIMIT 1",
        (material_id, effective_date.isoformat(), effective_date.isoformat()),
    ).fetchone()
    if header is None:
        return None
    items = connection.execute(
        "SELECT component_material, qty_per, scrap_pct FROM STPO WHERE bom_id = ? ORDER BY item_no",
        (header[0],),
    ).fetchall()
    return header[0], items


def run_mrp(
    connection: sqlite3.Connection,
    demand_rows: Iterable[dict[str, str]],
    plant: str = "1000",
) -> PlanningResult:
    """Net demand by material and due date, then explode planned in-house order quantities."""
    requirements: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for index, row in enumerate(demand_rows, start=2):
        material_id = (row.get("material_id") or "").strip()
        due_date = _iso_date(row.get("due_date", ""), f"demand row {index} due_date")
        try:
            quantity = float(row.get("quantity", ""))
        except (TypeError, ValueError) as exc:
            raise PlanningError(f"demand row {index} quantity must be numeric") from exc
        if not material_id or not math.isfinite(quantity) or quantity <= 0:
            raise PlanningError(f"demand row {index} needs a material_id and a positive quantity")
        _material_master(connection, material_id, plant)
        requirements[material_id].append((due_date, quantity))

    material_order = _topological_material_order(connection)
    planned_orders: list[PlannedOrder] = []
    netting_rows: list[MaterialNetting] = []
    order_counter = 1

    for material_id in material_order:
        events = sorted(requirements.get(material_id, []), key=lambda event: event[0])
        if not events:
            continue
        master = _material_master(connection, material_id, plant)
        opening = _opening_stock(connection, material_id, plant)
        safety = float(master[6])
        available = max(0.0, opening - safety)
        gross = sum(quantity for _, quantity in events)
        planned_receipts = 0.0

        for finish_date, needed_qty in events:
            if needed_qty <= available + 1e-9:
                available -= needed_qty
                continue

            shortage = needed_qty - available
            lot_size = int(master[5])
            order_qty = math.ceil((shortage - 1e-9) / lot_size) * lot_size
            available = order_qty - shortage
            planned_receipts += order_qty
            lead_days = _routing_lead_time(
                connection,
                material_id,
                plant,
                order_qty,
                finish_date,
                int(master[4]),
            )
            start_date = finish_date - timedelta(days=lead_days)
            order_category = "IN_HOUSE" if master[3] == "E" else "PURCHASE"
            order = PlannedOrder(
                planned_order_id=f"SIM-{order_counter:04d}",
                material_id=material_id,
                description=master[1],
                plant=plant,
                order_category=order_category,
                planned_qty=float(order_qty),
                base_uom=master[2],
                start_date=start_date.isoformat(),
                finish_date=finish_date.isoformat(),
                lead_time_days=lead_days,
            )
            planned_orders.append(order)
            order_counter += 1

            if master[3] == "E":
                bom = _active_bom(connection, material_id, start_date)
                if bom is None:
                    raise PlanningError(
                        f"In-house material {material_id} has no valid BOM on planned start date {start_date}"
                    )
                _, items = bom
                for item in items:
                    component = item[0]
                    component_qty = order_qty * float(item[1]) * (1 + float(item[2]) / 100)
                    _material_master(connection, component, plant)
                    requirements[component].append((start_date, component_qty))

        netting_rows.append(
            MaterialNetting(
                material_id=material_id,
                gross_requirement=round(gross, 6),
                opening_stock=round(opening, 6),
                safety_stock=round(safety, 6),
                planned_receipts=round(planned_receipts, 6),
                closing_projected_stock=round(available + safety, 6),
            )
        )

    connection.execute("DELETE FROM PLAF WHERE plant = ?", (plant,))
    connection.executemany(
        "INSERT INTO PLAF (planned_order_id, material_id, plant, order_category, planned_qty, "
        "start_date, finish_date, lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                order.planned_order_id,
                order.material_id,
                order.plant,
                order.order_category,
                order.planned_qty,
                order.start_date,
                order.finish_date,
                order.lead_time_days,
            )
            for order in planned_orders
        ],
    )
    connection.commit()
    return PlanningResult(tuple(planned_orders), tuple(netting_rows))


def read_demand_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"material_id", "due_date", "quantity"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise PlanningError("Demand CSV must contain columns: material_id, due_date, quantity")
        return list(reader)


def write_orders_csv(path: str | Path, orders: Iterable[PlannedOrder]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = list(PlannedOrder.__dataclass_fields__.keys())
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for order in orders:
            writer.writerow(asdict(order))
