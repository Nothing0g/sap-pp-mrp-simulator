from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pp_mrp.database import connect, initialize
from pp_mrp.engine import PlanningError, run_mrp


class MRPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp_dir.name) / "test.sqlite3")
        initialize(self.connection, reset_demo_data=True)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp_dir.cleanup()

    def plan(self, material: str = "FORK-100", due_date: str = "2026-12-10", quantity: int = 12):
        return run_mrp(
            self.connection,
            [{"material_id": material, "due_date": due_date, "quantity": str(quantity)}],
        )

    def test_multilevel_bom_explosion_creates_in_house_and_purchase_orders(self) -> None:
        result = self.plan(quantity=30)
        materials = {order.material_id for order in result.orders}
        self.assertIn("FORK-100", materials)
        self.assertIn("FORK-110", materials)
        self.assertIn("LEG-L", materials)
        self.assertIn("SEAL-KIT", materials)
        self.assertTrue(any(order.order_category == "IN_HOUSE" for order in result.orders))
        self.assertTrue(any(order.order_category == "PURCHASE" for order in result.orders))

    def test_stock_is_netted_but_safety_stock_is_protected(self) -> None:
        result = self.plan(quantity=12)
        order = next(order for order in result.orders if order.material_id == "FORK-100")
        self.assertEqual(order.planned_qty, 9)  # 12 gross demand less 3 unrestricted units.
        leg_netting = next(row for row in result.netting if row.material_id == "LEG-L")
        self.assertEqual(leg_netting.opening_stock, 18)
        self.assertEqual(leg_netting.safety_stock, 4)
        self.assertGreaterEqual(leg_netting.closing_projected_stock, 4)

    def test_lot_size_rounding_and_explosion_use_planned_order_qty(self) -> None:
        self.connection.execute("UPDATE MARC SET lot_size = 10 WHERE material_id = 'FORK-100'")
        self.connection.execute("UPDATE MARD SET unrestricted_qty = 0 WHERE material_id = 'FORK-100'")
        self.connection.commit()
        result = self.plan(quantity=3)
        root = next(order for order in result.orders if order.material_id == "FORK-100")
        subassembly = next(order for order in result.orders if order.material_id == "FORK-110")
        self.assertEqual(root.planned_qty, 10)
        self.assertEqual(subassembly.planned_qty, 10)  # Safety stock leaves no subassembly stock available.

    def test_routing_and_fixed_lead_time_offset_the_start_date(self) -> None:
        result = self.plan(quantity=12)
        root = next(order for order in result.orders if order.material_id == "FORK-100")
        self.assertEqual(root.finish_date, "2026-12-10")
        self.assertEqual(root.lead_time_days, 2)
        self.assertEqual(root.start_date, "2026-12-08")

    def test_external_material_is_not_bom_exploded(self) -> None:
        result = self.plan(material="LEG-L", quantity=50)
        self.assertEqual([order.material_id for order in result.orders], ["LEG-L"])
        self.assertEqual(result.orders[0].order_category, "PURCHASE")

    def test_cycle_is_reported_instead_of_recursing_forever(self) -> None:
        self.connection.execute(
            "INSERT INTO STKO (bom_id, parent_material, alternative, valid_from, valid_to) "
            "VALUES ('BOM-CYCLE', 'FORK-110', 2, '2025-01-01', '9999-12-31')"
        )
        self.connection.execute(
            "INSERT INTO STPO (bom_id, item_no, component_material, qty_per, scrap_pct) "
            "VALUES ('BOM-CYCLE', 99, 'FORK-100', 1, 0)"
        )
        self.connection.commit()
        with self.assertRaisesRegex(PlanningError, "BOM cycle detected"):
            self.plan()

    def test_missing_valid_bom_is_explained(self) -> None:
        self.connection.execute("UPDATE STKO SET valid_to = '2025-12-31' WHERE bom_id = 'BOM-FORK-100'")
        self.connection.commit()
        with self.assertRaisesRegex(PlanningError, "no valid BOM"):
            self.plan()

    def test_invalid_date_and_nonpositive_demand_are_rejected(self) -> None:
        with self.assertRaisesRegex(PlanningError, "ISO date"):
            run_mrp(self.connection, [{"material_id": "FORK-100", "due_date": "12/10/2026", "quantity": "1"}])
        with self.assertRaisesRegex(PlanningError, "positive quantity"):
            run_mrp(self.connection, [{"material_id": "FORK-100", "due_date": "2026-12-10", "quantity": "0"}])


if __name__ == "__main__":
    unittest.main()
