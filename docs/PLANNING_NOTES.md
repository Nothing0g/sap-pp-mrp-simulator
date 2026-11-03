# Planning Notes and User Guide

## Scenario

A make-to-stock plant plans a small batch of front suspension fork assemblies for two requested receipt dates. The example is discrete manufacturing. The planner uses the sample material master, multi-level BOMs, inventory, simple routings and work-centre capacity figures to create a transparent list of suggested replenishments.

## Process flow

```text
Demand CSV
   -> validate material, date and quantity
   -> determine parent-before-component sequence from the BOM graph
   -> net each dated requirement against unrestricted stock, preserving safety stock
   -> round any shortage to the material's lot-size multiple
   -> create simulated in-house / purchase planned-order suggestions
   -> offset start dates by lead time and simple route-duration estimate
   -> explode the planned quantity of in-house orders into dated component requirements
   -> persist suggestions to local PLAF table and export CSV
```

## Selected object mapping

| Learning object | Fields used here | Purpose in this exercise |
|---|---|---|
| `MARA` | material ID, description, base unit | Material identity and display text |
| `MARC` | plant, procurement type, planned lead time, lot size, safety stock | Plant-specific planning controls |
| `MARD` | plant, storage location, unrestricted quantity | Inventory available for simple netting |
| `STKO` / `STPO` | parent, alternative, validity, component, quantity, scrap | Multi-level BOM structure |
| `CRHD` | work centre and available minutes/day | Capacity denominator for a rough route-time estimate |
| `PLKO` / `PLPO` | routing validity, operation, work centre, setup and run time | Simple routing-based lead-time floor |
| `PLAF` | planned-order material, plant, quantity and dates | Local simulated replenishment suggestions |
| `AFKO` / `AFPO` | minimal downstream order header/item examples | Included as a concept only; not written by the MRP run |

Object names and meanings are inspired by SAP. Column definitions and behavior are deliberately simplified and are not a compatible SAP schema.

## Simplifying assumptions and fit boundaries

- One plant per run; one base unit per material; positive demand only.
- Stock is a snapshot. The simulation does not model reservations, open purchase orders, scheduled receipts, batch/serial stock, scrap postings, or inventory status beyond unrestricted stock.
- Safety stock is protected before demand is netted. Surplus caused by fixed lot-size multiples can cover later dated demand in the same run.
- Requirements are processed in date order for each material. Multiple BOM parents are handled by a parent-before-component graph order.
- The lowest-numbered valid BOM alternative is selected. Effectivity is checked for the simulated parent start date.
- Any cycle in the stored BOM graph stops planning. An in-house shortage without an effective BOM stops with an actionable error.
- Lead-time offsets use calendar days. Routing duration is a rough sum of per-operation setup plus run time divided by stated available minutes/day, rounded up; planned lead time is a minimum. This is not workday/calendar scheduling and does not sequence or level capacity.
- The engine produces simulated replenishment suggestions only. Purchase suggestions are not MM purchase requisitions; in-house suggestions are not converted to production orders.

### Cross-functional touchpoints (not implemented integrations)

- **MM:** an external-procurement shortage could be handed to purchasing as a proposed replenishment; no requisition or vendor process is created here.
- **QM:** incoming inspection or in-process inspection requirements could be attached to material/operation master data; no inspection lots or quality decisions are modeled.
- **PM:** equipment availability could constrain a work centre; no maintenance orders or downtime calendar are modeled.
- **FI/CO:** material and activity valuation/costing could consume quantities and operation times; this simulation does not calculate costs or post accounting entries.
- **PLM / PEO / PLMSI:** engineering revisions, manufacturing engineering change, and system integration would require additional lifecycle objects and governance. They are outside this project.

## Test-plan summary

Automated tests under `tests/` cover: multilevel explosion; in-house versus external replenishment; unrestricted-stock and safety-stock netting; planned-lot rounding and explosion of the rounded order quantity; routing/lead-time date offsets; cycle detection; missing effective BOM; and invalid demand dates/quantities. Run them with `python3 -m unittest discover -s tests -v`.

A useful manual check is to compare the root assembly's gross demand with its opening stock and then trace its planned order quantity into the subassembly and purchased component requirements. Keep a copy of the demand CSV with any result so the run can be reproduced.

## Quick user guide

1. From the repository root, run `python3 -m pp_mrp --reset` to reload the sample data and execute the bundled demand.
2. Read the terminal summary, then open `output/planned_orders.csv` in a spreadsheet or text editor.
3. Check `order_category`, quantity, material, finish date and start date. All dates are calendar dates in this simplified example.
4. To test a new scenario, edit or copy `data/demand.csv`, retaining its three required headers, then pass its path with `--demand` and choose an output path with `--output`.
5. A missing material, invalid date/quantity, BOM cycle, or in-house shortage without an effective BOM ends the run with an explanatory error. Correct the input or sample master data and rerun.
6. To restore the original sample, run with `--reset` again. The SQLite file and generated output are local and can be removed without affecting the source data.
