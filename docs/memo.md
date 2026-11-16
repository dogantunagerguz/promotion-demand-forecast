# Promotion forecasting: why P18 missed, four beliefs, and the P19 forecast

Doğan Tuna Gerguz · 24 October 2026 · Claim codes match the Claims Ledger.

**Summary.** The P18 forecast looked right in total because two errors cancelled: it under-forecast demand in the promotion week by 18 % and over-forecast the two weeks after by 15 % (against sales) [T0]. The largest recurring cause is a promotion lift learned per category that knows neither the store format nor the days on which shelves were empty; the largest one-off cause is the April supply disruption inside the baseline window. Of the four commercial beliefs, two are contradicted by the data (discount depth, fast sellers), one is only partly true (category cannibalisation), one is true but not for the reason claimed (remodeled stores). For the P19 promotion week I forecast 19,848 units of demand for the 23 promoted items, with an 80 % interval of 18,100–21,900.

A note on the yardstick. On a day when the shelf emptied, sales are only a lower bound on demand. Throughout, *demand* means sales on days when the shelf stayed stocked, and on emptied days an estimate from the same promotion's stocked store-days; the estimate is made for promotion weeks, and for other periods demand is taken as sales. A forecast that moves away from sales is not necessarily worse; it can be closer to demand. All sales-based numbers are reported next to demand-based ones.

## 1. Why the P18 forecast missed

**Where.** The forecast rows were split into five segments (the fifth, promoted items on other days, is at 0.97 and omitted below) and compared with sales and with demand.

| Segment (26 May – 6 Jul) | Sales | Demand | Forecast / sales | Forecast / demand |
|---|---|---|---|---|
| Promoted items, promotion week | 10,642 | 13,298 | 1.02 | 0.82 |
| Promoted items, next two weeks | 7,857 | 7,857 | 1.15 | 1.15 |
| Same category, not promoted, promotion week | 8,350 | 8,350 | 1.04 | 1.04 |
| All other items (baseline check) | 275,771 | 275,771 | 0.96 | 0.96 |

By format in the promotion week (forecast / demand): Hyper 0.73, Super 0.92, Express 1.12 (against sales Express is 1.66). By category: 13 → 0.64, 1 → 0.77, 7 → 0.82, 18 → 0.84, 3 → 0.99. By day: under every day; on the Sunday, sales were 903 against a demand of 1,835 — the day the shelves were empty.

**Causes, ranked by business impact.**

1. **The lift ignores the store format (lift; under and over).** Hyper stores respond to promotions 1.5 times as strongly as Express stores (mean lift per item-promotion-format: Hyper 2.54, Super 2.12, Express 1.69; 649 events). One category lift gave Hyper too little and Express too much. The Hyper gap is about 2,100 units in one week, the largest error that recurs in every promotion; the baseline shortfall of cause 5 is bigger in units (≈ 10,900 over six weeks, 9,600 in categories 1, 9, 11) but one-off [C3].
2. **The lift was measured on sales that include empty-shelf days (lift; under).** Excluding those days raises the same events' lift from 2.54 to 2.94 in Hyper and 2.12 to 2.25 in Super (647 events). The method learns its lift from raw sales, so it starts low [C7].
3. **No post-promotion dip (after the promotion; over).** After a promotion, sales fall to about 73 % of normal in the first week and 89 % in the second (250 events). The method treats those weeks as normal and over-forecast the two weeks after P18 by about 1,200 units against sales [C5].
4. **Discount depth is ignored (lift; under).** Category 13 ran at 40 % in P18 after 20–30 % in its history; it received the category's old lift and got 64 % of its demand. Section 2 shows that the same item at a deeper discount does sell more [C2, B3].
5. **The baseline is 4 % low (baseline; under).** For items not on promotion the forecast was 0.96 of sales in Hyper and Super and 0.98 in Express. Two mechanisms: from 7 April to 4 May opening stock fell by 12 % and the empty-shelf rate rose from 11 % to 18 % (the same weeks of 2024 are flat), and these four weeks are half of the baseline window — categories 1, 9 and 11 were hit hardest; and empty-shelf days enter the average as low sales. I could not separate the two shares. Excluding empty-shelf days recovers about half of the April effect (company −20 % vs this method −6 to −10 % in categories 1, 9, 11) [C1].
6. **No category cannibalisation (small).** Not-promoted items in the promoted categories were over-forecast by 4 %, about 330 units [B4].

**Explanations considered and ruled out.** (a) April was a demand drop: no — stock fell, sales did not rise, shelves emptied more often; a supply problem. (b) Seasonality: for non-promoted items the forecast/sales ratio is 0.96–0.98 in every format and stable week to week. (c) Excluding empty-shelf days biases the lift because those are the high-demand days: excluded vs filled lifts differ by about 4 %; empty shelves follow the delivery cycle (on normal days 6 % on Thursday and 26 % on Sunday; on promotion days 5 % and 47 %), not demand. (d) Six items launched on 3 March diluted the baseline: their ramp-up ended on 24 March, before the window; their P18 errors are between −6 % and +4 %.

**What I would change in the method.** Three things, all applied in Section 3: exclude empty-shelf days from the baseline and the lift; learn the lift by format × category with a fallback to category and format where history is thin; apply measured factors to the two weeks after a promotion. And one cheap check at the forecast origin: if the last three weeks differ markedly from the eight-week average (in May they were normal, April was low), raise a flag — that check would have caught the April effect before the forecast went out.

## 2. The commercial team's four beliefs

**"Fast-selling items respond less, so promoting them is pointless." True in ratio, false in units [B1].** Splitting 250 item-promotions into four groups by normal sales rate (63 events in the extreme groups), the slowest group has a lift of 2.40 and the fastest 2.24 — a small difference. But the extra units a promotion brings are 16 per day in the slow group and 99 in the fast group. Stock and revenue are planned in units; the "pointless" part is not supported. Profitability was not measured. Confidence: high for the units difference.

**"Stores remodeled in 2024 respond better." The difference is real; the cause is not shown [B2].** In 2025 promotions the remodeled stores have higher lifts in Hyper and Super (Hyper 3.13 vs 2.63; Mann-Whitney p = 0.009 on 16 + 16 store-promotions, which treats a store's promotions as independent) and equal lifts in Express (1.63 vs 1.63). The same gap existed in 2023, before the remodel (Hyper 3.37 vs 2.83, Super 2.29 vs 1.95). The 2023 → 2025 change of the same stores does not differ between the groups (30 stores, p = 0.32: no evidence of a difference, not proof of equality). The programme appears to have selected stores that already responded well. Confidence: medium for the difference, low for the cause.

**"Discount depth barely matters; 20 % sells like 40 %." Contradicted [B3].** Grouped by discount, the averages do look flat between 15 % and 35 % — but that comparison cannot separate the discount from which items received it. Comparing the same item and format at two different discounts (293 pairs, 55 items), the deeper side has the higher lift in 66 % of pairs (sign test, p < 10⁻⁷, which overstates the evidence because pairs sharing a promotion are not independent; the 66 % share and the direction in every format are the robust part); a 10-point deeper discount multiplies the lift by about 1.11 (1.08 with P18 excluded; same direction in every format). Confidence: high for the direction, medium for the size.

**"A promotion takes sales from every other item in its category." Partly [B4].** Over 72 category-promotion events in 18 promotions, the neighbours' loss is about 14 % of the promoted items' extra sales. Categories 4, 7 and 10 show no loss; the strongest losses are in categories 5 and 11 (neighbours at 79 % of their baseline). Categories 8 and 14 have one promotion each and cannot be judged. Confidence: medium, by category.

## 3. The P19 forecast

**Method.** Daily demand = baseline × weekday factor × lift (promotion days) × post-promotion factor (two weeks after) × category-neighbour factor (not-promoted items of a promoted category, promotion week).
- *Baseline*: store-item, the 8 weeks before the origin (14 July); promotion days, empty-shelf days and the 14 days after a promotion excluded; mean of the remaining days × the store's weekday profile.
- *Lift*: format × category, all 18 past promotions, stocked-shelf store-days only: promotion-week sales ÷ baseline on the same store-days, summed (volume-weighted; the ledger's descriptive lifts are averages of event ratios and therefore differ slightly). A cell with fewer than 3 item-promotions falls back to category, then format, then chain. The planned discount adjusts the cell lift by 1.11 per 10 points above the cell's historical mean discount (B3).
- *After the promotion*: × 0.74 in week one, × 0.89 in week two. *Category neighbours*: category factors (B4).
- *Backtest*: the same method applied to P07–P18 at each promotion's own origin. On stocked-shelf store-days (sold ÷ forecast) it is within 5 % for 11 of 12 promotions; with empty-shelf days filled, demand is above the forecast in 11 of 12 promotions (+5 to +12 %; P07 −1 %), 7 % on average — the demand hidden by empty shelves. The promotion-week forecast is multiplied by 1.073 (ledger, section 3).

**How the findings shaped the forecast.**

| Finding | Response in the forecast |
|---|---|
| C3 format, C7 empty-shelf lift | Lift by format × category from stocked-shelf days |
| C1 April disruption, empty days in the baseline | Empty-shelf days excluded from every baseline |
| C5 post-promotion dip | Weeks +1 and +2 forecast with measured factors |
| B3 discount depth | Lift adjusted for the planned discount |
| B4 cannibalisation | Category factors for neighbours; none in 4, 7, 10 |
| B1 fast sellers, B2 remodel | No extra multiplier: the store-item baseline carries the speed, and B2 showed no causal effect |

**Commitment.** Promoted items, 4–10 August: **19,848 units** (Hyper ≈ 11,600, Super ≈ 7,200, Express ≈ 1,100); **80 % interval 18,100–21,900**. The interval has two parts: the central 80 % of the twelve backtest demand/forecast ratios (1.05–1.10) for the 47 % of the volume that has a precedent, and for the other 53 % — category 17, never promoted, and eight items at 45–50 % while history never exceeded 40 % — the spread of category lifts within a format (±17 %) added on top.

**Where I am least confident.** The four category-17 items (27 % of the volume): no promotion history, so a format-level lift, and a discount 19 points deeper than that lift's history. Then the four category-10 items at 45–50 %. These eight items are the reason the interval is as wide as it is. A smaller point: the weekday profile is learned from stocked-shelf days, which under-represents Sundays; in the backtest weekends are about 10 % over and Mondays about 10 % under, so weekly totals are right and the split across days less so. An independent second implementation of the same structure (built with ChatGPT) gives the P18 promotion week within 3 % of this one before calibration.

**Bonus: stock.** One lost unit costs 1.00, one leftover 0.30, so stock should cover demand with probability 1 / (1 + 0.30) = 77 %. In the backtest the store-item weekly demand/forecast ratio has its 77th percentile at 1.40 in Hyper, 1.53 in Super and 1.69 in Express; order = the uncalibrated weekly forecast × that multiplier, rounded up (the ratios already contain the 7 % calibration): **27,345 units** over 621 store-item pairs (`order_P19.csv`).

**Data I would want.** Store delivery schedules (to turn the Sunday effect and the empty-shelf cycle into a rule), remodel dates per store (B2), promotion announcement dates and prices. Delivery schedules would also test the bonus assumption of one delivery before the week.

---
*Appendix: files.* `forecast_p19.py` (forecast, backtest, interval, order); `claims_analysis.ipynb` (every ledger claim and the additional checks); outputs in `output/`.
