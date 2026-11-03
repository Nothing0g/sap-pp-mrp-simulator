"""Command-line entry point: python -m pp_mrp."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .database import connect, initialize
from .engine import PlanningError, read_demand_csv, run_mrp, write_orders_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SAP-style bike suspension MRP simulation.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "mrp_demo.sqlite3"), help="SQLite database path")
    parser.add_argument("--demand", default=str(PROJECT_ROOT / "data" / "demand.csv"), help="Demand CSV path")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "output" / "planned_orders.csv"), help="Planned-order CSV path")
    parser.add_argument("--plant", default="1000", help="Plant key (default: 1000)")
    parser.add_argument("--reset", action="store_true", help="Reset and reseed the demo database before planning")
    args = parser.parse_args()

    try:
        with connect(args.db) as connection:
            seeded = initialize(connection, reset_demo_data=args.reset)
            result = run_mrp(connection, read_demand_csv(args.demand), plant=args.plant)
        write_orders_csv(args.output, result.orders)
    except (OSError, PlanningError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if seeded:
        print("Loaded the sample master data.")
    print(f"Plant {args.plant}: {len(result.orders)} simulated planned orders")
    print(f"Planned-order CSV: {Path(args.output).resolve()}")
    if result.orders:
        print(f"{'ID':<10} {'MATERIAL':<12} {'TYPE':<10} {'QTY':>7} {'START':<12} {'RECEIPT':<12}")
        for order in result.orders:
            print(
                f"{order.planned_order_id:<10} {order.material_id:<12} "
                f"{order.order_category:<10} {order.planned_qty:>7g} "
                f"{order.start_date:<12} {order.finish_date:<12}"
            )
    else:
        print("No replenishment is required for this demand and stock position.")
    print("Note: results are simulated planning suggestions, not SAP transactions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
