# Development / Debugging Log

This log records issues observed while building and testing this learning simulation. The first test run had three failures; all three came from test scenarios that did not match their expected stock conditions. The planner's inventory netting behaved as designed. The fixtures/assertions were corrected and the suite then passed.

## 2026-11-03 — First automated test run

**What happened:** `python3 -m unittest discover -s tests -v` reported three failing tests out of eight.

1. **External-procurement test produced no planned order.** I asked for two `LEG-L` units, but sample unrestricted inventory was already sufficient after safety stock. The planner correctly returned no replenishment; my test expected a purchase suggestion without creating a shortage.
   - **Fix:** Changed the test demand to 50 units so it exercises an actual shortage and then asserts that the result is a purchase suggestion only (not a BOM explosion).
2. **Lot-size test expected eight subassemblies.** I mentally subtracted the one on-hand unit but overlooked the two-unit safety stock. Since stock below safety stock is unavailable in this exercise, no subassembly stock could be netted; the 10-unit parent lot therefore required 10 subassemblies.
   - **Fix:** Corrected the expected subassembly quantity to 10 and made the safety-stock reasoning explicit in the test comment.
3. **Multilevel test did not reach the left/right leg procurement level.** Twelve fork units netted to a nine-unit parent planned order because three finished forks were in stock. The leg inventory could cover the resulting component need above the protected safety stock, so no leg order was expected.
   - **Fix:** Raised the test demand to 30 units, creating a genuine shortage at the lower-leg level and allowing the assertion to exercise a deeper BOM level.

**Verification after the fixes:** all 8 automated tests passed. The bundled CLI run also completed and wrote 17 simulated planned-order rows for plant `1000` to the ignored local output CSV.

**Takeaway:** For MRP tests, calculate available stock as unrestricted stock minus protected safety stock before deciding whether a demand scenario should produce a replenishment. This is a test-fixture correction, not a claim that the planner implementation had a bug.
