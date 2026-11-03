# SAP-Style PP / MRP Simulation — Bicycle Suspension Assembly

A small, explainable Python + SQLite simulation of selected SAP Production Planning (PP) master-data concepts. It explodes a multi-level bill of material (BOM), nets dated demand against unrestricted stock while protecting safety stock, rounds shortages to lot-size multiples, and calculates start dates by offsetting finish dates with planned lead time and a simple routing-duration estimate.

> **Project scope:** This is an independent simulation inspired by selected PP planning concepts. It is not SAP software and does not connect to a live SAP system; the master data and outputs are illustrative.

## What it demonstrates

- A discrete-manufacturing, make-to-stock scenario for a front suspension fork assembly.
- Multi-level BOM explosion and component demand dated from the parent planned order's start date.
- Stock netting with safety-stock protection and lot-size rounding.
- Planned-order suggestions for in-house materials and purchase suggestions for externally procured materials.
- Lead-time offsets using material planned lead time and a basic route-duration estimate from work-centre capacity.
- Input validation, missing-master-data/BOM errors, BOM-cycle detection, automated tests, and CSV output.

The schema uses a small SQLite subset inspired by `MARA`, `MARC`, `MARD`, `STKO`, `STPO`, `CRHD`, `PLKO`, `PLPO`, and `PLAF`. Simplified `AFKO`/`AFPO` tables are present only to show the downstream production-order concept; this project stops at simulated planned orders and does not create production orders.

## Run locally

**Requirements:** Python 3.10 or newer. The application and tests use only the Python standard library; there is no database server or `pip install` step.

```bash
git clone https://github.com/Nothing0g/sap-pp-mrp-simulator.git
cd sap-pp-mrp-simulator
python3 -m pp_mrp --reset
```

`--reset` recreates the sample master data in `data/mrp_demo.sqlite3`, runs the sample demand in `data/demand.csv`, and writes `output/planned_orders.csv`. The database and generated CSV are intentionally ignored by Git. Omit `--reset` to reuse the current local database.

Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

Plan a different CSV or write to another output path:

```bash
python3 -m pp_mrp --demand path/to/demand.csv --output output/my_plan.csv --plant 1000
```

Demand CSV headers must be `material_id,due_date,quantity`; dates use `YYYY-MM-DD`, and quantities must be positive. For example:

```csv
material_id,due_date,quantity
FORK-100,2026-12-10,12
FORK-100,2026-12-17,8
```

If you move the project directory, run commands from the repository root. No credentials or external services are required.

## Result interpretation

Each output row is a **suggested simulated replenishment**, not an SAP-created order. `IN_HOUSE` means a shortfall for an internally made material; `PURCHASE` means a shortfall for an externally procured material. `finish_date` is the requirement date; `start_date` is the finish date minus the estimated lead time in **calendar days**. This demo does not promise finite-capacity scheduling or shop-floor feasibility.

The sample data is intentionally small and illustrative. The material IDs, quantities, stock, dates, BOMs, routes, and work centres are invented for this exercise.

## Sample planned-order report

The bundled run produced 17 simulated planned orders. A few rows from the generated `output/planned_orders.csv`:

| Planned order | Material | Category | Qty | Start date | Finish date |
|---|---|---|---:|---|---|
| `SIM-0001` | `FORK-100` | `IN_HOUSE` | 9 | 2026-12-08 | 2026-12-10 |
| `SIM-0002` | `FORK-100` | `IN_HOUSE` | 8 | 2026-12-15 | 2026-12-17 |
| `SIM-0007` | `SEAL-KIT` | `PURCHASE` | 20 | 2026-12-11 | 2026-12-15 |

## Project map

```text
pp_mrp/engine.py       MRP netting, BOM explosion, routing offset, validation
pp_mrp/database.py    SQLite initialization and sample-data loading
pp_mrp/__main__.py    Command-line interface
sql/schema.sql        SQLite schema modeled on selected SAP PP objects
sql/seed.sql          Example master data and BOMs
data/demand.csv       Sample independent demand
tests/                Automated simulation tests
docs/PLANNING_NOTES.md Process/object mapping, assumptions, and user guide
docs/DEBUGGING_LOG.md Actual issues found and resolved during this build
```

## Relevance to the role description

This exercise provides a discussion artifact for discrete-manufacturing process analysis, PP master-data relationships, a simplified data model, validation, troubleshooting, test planning, and user instructions. It identifies conceptual relationships to the JD-named PLM, PEO, and PLMSI areas without claiming those integrations are implemented. It does **not** claim a live SAP connection or production deployment.

See [Planning notes and user guide](docs/PLANNING_NOTES.md) and [development/debugging log](docs/DEBUGGING_LOG.md).
