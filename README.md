# Promotion demand forecasting for a retail chain

A take-home case from a retail-analytics company, October 2026. Two years of daily sales and opening stock for 30 stores (Hyper, Super, Express), 180 items in 18 categories, 18 past promotions. The brief had four parts:

1. explain why the company's forecast for the last promotion (P18) missed,
2. test four beliefs the commercial team plans around,
3. forecast daily **demand** — what customers would have bought had the shelf never run empty — for the next promotion week (P19) plus the two weeks after, with an 80 % interval,
4. decide how many units each store should hold at the start of the week.

**Result:** 19,848 units of demand for the 23 promoted items in the P19 week, 80 % range 18,100–21,900; 27,345 units of stock across 621 store-item rows.

The raw data belongs to the company and is not included. Everything the method produced — tables, factors, the forecast file — is in `output/`, and the notebook keeps its outputs, so the analysis can be read without rerunning it.

## The one idea

Sales can never exceed what is on the shelf. On a day when sales reached the opening stock, the data shows the stock, not the demand. That happened on one regular day in ten in Hyper and Super stores, one in five in Express, and on a quarter of all store-days in a promotion week. So:

- wherever the method *learns* (baseline, lift, after-effects), empty-shelf days are left out;
- wherever the method is *judged* (backtest), demand on an emptied day is estimated from the same item's stocked store-days in the same promotion week — the days that sold at least as much as the emptied day's opening stock.

In the P18 week, 10,642 units were sold; the demand estimate is 13,298 — a quarter higher.

## Why the P18 forecast missed

Against sales, the P18 total was within 2 %. Against demand, the promotion week was 18 % under and the two weeks after were 15 % over; the two cancelled. Six causes, in order of size:

| Cause | Evidence |
| --- | --- |
| One lift for every store format | Hyper lifts 2.54×, Super 2.12×, Express 1.69× (649 item-promotion-format events); Hyper was 27 % under, Express 12 % over |
| Lift learned from raw sales | Measured on stocked days the Hyper lift is 2.94×, not 2.54× |
| No post-promotion dip | Sales run at 73 % of normal in the first week after a promotion and 88 % in the second (250 item-promotions) |
| Discount depth ignored | Category 13 ran at 40 % off after 20–30 % in its history, got its old lift, and 64 % of its demand |
| A supply disruption inside the baseline window | In April 2025 opening stock in categories 1, 9 and 11 fell by ~70 %; their empty-shelf rate went from 12 % to 49 %; the baseline learned from those days (one-off) |
| Category neighbours | Non-promoted items in a promoted category lose about 14 % of the promoted items' gain |

## The four beliefs

| Belief | Verdict | Test |
| --- | --- | --- |
| "Fast sellers respond less, so promoting them is pointless" | True in ratio, false in units | 250 item-promotions in speed quartiles: lift 2.40× (slowest) vs 2.24× (fastest), but 16 vs 99 extra units a day |
| "Stores remodelled in 2024 respond better" | The gap is real; the remodel is not shown to be the cause | Within Hyper, 4 remodelled vs 4 other stores × 4 promotions: 3.13× vs 2.63× (Mann-Whitney, p = 0.009) — but 3.37× vs 2.83× already in 2023, and both groups moved by the same factor since (p = 0.32) |
| "Discount depth barely matters" | Contradicted | Pooled by discount level the lift looks flat, because different items got different discounts. Same item, same format, two discounts: 293 pairs, the deeper discount lifts more in 66 % (sign test p < 10⁻⁷); ×1.11 per 10 points |
| "A promotion takes sales from every other item in its category" | Partly | 72 category-promotion events: categories 5 and 11 lose about a fifth, 4, 7 and 10 nothing detectable, 8 and 14 have one promotion each — no verdict |

## The method

The company's skeleton — baseline × weekday profile × lift — with each part learned differently:

```
forecast(store, item, day) = baseline × weekday_profile × lift* × post × neighbour
```

| Part | How it is learned |
| --- | --- |
| Baseline (store × item) | Mean daily sales over the 8 weeks before the forecast date, excluding promotion days, empty-shelf days and the 14 days after a promotion |
| Weekday profile (store) | Same window, same kept days, average weekday = 1 |
| Lift | Σ promotion-week sales ÷ Σ baseline on stocked days, per **format × category**; fewer than 3 records → category → format → chain. Then × 1.113 ^ ((plan discount − cell's mean discount) / 0.10) |
| After the promotion | × 0.73 in days 1–7, × 0.88 in days 8–14 (chain-wide, stocked days) |
| Category neighbours | × the category's measured factor when it rests on ≥ 3 promotions, else the chain factor 0.89 |
| Calibration | The method was backtested on 12 past promotions, each forecast at its own date with earlier data only. Demand ran 7 % above the raw forecast every time (ratios 0.99–1.12), so promoted items' promotion-week rows are multiplied by 1.073 |
| 80 % interval | Volume with a precedent (47 %): the backtest ratios' 10th–90th percentiles, 1.05–1.11. Volume without (category 17, never promoted, and items at 45–50 % off): ± 17 %, the spread of category lifts within a format. The two parts are added |
| Order quantity | A lost sale costs 1.00, a leftover 0.30, so stock should cover demand with probability 1/1.30 = 0.77. Per format, the 77th percentile of the backtest's store-item demand ÷ forecast ratios (Hyper 1.40, Super 1.53, Express 1.69) × the raw weekly forecast, rounded up |

### Backtest

| Promotion | P07 | P08 | P09 | P10 | P11 | P12 | P13 | P14 | P15 | P16 | P17 | P18 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demand ÷ forecast | 0.99 | 1.06 | 1.05 | 1.08 | 1.05 | 1.11 | 1.09 | 1.10 | 1.09 | 1.12 | 1.09 | 1.06 |

P01–P06 are not backtested: too little history before them to learn a lift.

## Limits I know of

- The interval's coverage is not validated — twelve promotions are too few.
- Category 17 is 27 % of the P19 volume and has never been promoted; its lift comes from the format level, taken 19 points deeper in discount than that format's history. Two uncertainties on top of each other.
- The 45–50 % discounts lie beyond the range the discount slope was measured on.
- The weekday profile comes from stocked days, so weekends run a little high and Mondays low; which day the units sell also depends on delivery timing the data does not show. Weekly totals are more reliable than the daily split.
- Neighbours' own promotion weeks stay in their baseline — a small, deliberate simplification.
- The Mann-Whitney test treats store-promotions as independent; each store appears four times, so p = 0.009 is optimistic.

## What I'd do differently

I asked the company for feedback after the case and got a detailed answer. Six points, with what I plan to do about each:

1. **Treat sold-out days as censored, not missing.** I dropped sold-out days when learning the baseline and filled them when measuring demand. Both rest on the days that did *not* sell out — which tend to be the quieter days — so the baseline understates normal demand, and my own check (drop vs fill, about 4 %) could not see it, because both sides share the same blind spot. A sold-out day says "demand was at least this much"; that calls for a censored estimator. *Planned: Kaplan-Meier mean demand on the baseline window, validated on simulated data — notebook 2.*
2. **Apply a correction where its cause sits.** The backtest found demand 7 % above the forecast, and I corrected only the promoted items' promotion week — where I had measured it. If the cause is in the baseline, every row is affected. I had a segment-by-segment check half done and did not finish it. *Planned: measure the gap per segment and apply what each one shows.*
3. **Check the shape of an effect before extrapolating.** I measured a constant ×1.11 per 10 discount points and stretched it to 45–50 %, where there is no history. Response curves usually flatten. *Planned: fit a saturating curve within items and compare the two at 45–50 % — notebook 3.*
4. **Look at the shelf before ordering.** The data has opening stock for every store-item-day; its maximum says how much a shelf holds. I never looked. *Planned: order = min(statistical order, shelf capacity) — notebook 3.*
5. **No evidence, no adjustment.** Category 17 had never been promoted; its neighbours got the chain-wide factor by default. Borrowing a number is a choice; a wider interval would have been the more honest one.
6. **Package the evidence; write lighter.** Two files cited in the AI log are not in the package (they lived in a separate workspace). And the memo is dense — a planner, not a data scientist, should be able to read it.

Points 1, 3 and 4 are the next notebooks in this repository; each will be added as a commit with its results in this section.

## Repository

| Path | What it is |
| --- | --- |
| `forecast_p19.py` | The whole pipeline: baseline, lift tables, factors, forecast, backtest, calibration, interval, order. ~320 lines, pandas only |
| `claims_analysis.ipynb` | Every claim above, with the cell that produced it, plus the additional checks (P18 comparison, discount pairs, beliefs, April supply, empty-shelf treatment) |
| `scripts/` | Stand-alone versions of the belief tests, the discount test, the empty-shelf check and the P18 comparison |
| `output/` | What the pipeline and the notebook write: the P19 forecast (`forecast_P19.csv`, 101,304 rows), the order file, lift cells and records, factors, backtest tables, totals and interval |
| `docs/` | The memo, the slide deck, and the claims ledger with the AI log |
| `data/` | Not included; `data/README.md` gives the schema |

### Running it

```
pip install -r requirements.txt
python forecast_p19.py data output      # ~25 s after the first run (the daily table is cached as output/daily.pkl)
```

Then open `claims_analysis.ipynb` and run it top to bottom; it imports `forecast_p19` and reads `output/`.

## How the work was done

The code was written with AI assistance (Claude; ChatGPT/Codex for the early exploration and the Power BI measures) and every number was checked by hand or cross-checked with a second method: the company's category lift reproduced exactly, the lift table recomputed from the raw records, the calibration recomputed from the twelve ratios, the neighbour factor checked against one promotion by hand. Twice the AI's first answer was wrong in a way the data showed — a neighbour factor of 1.39 that had left the promoted items inside the neighbour group, and a post-promotion window measured against the wrong calendar — and `docs/claims_ledger_and_ai_log.md` records both, together with the prompts that shaped the decisions and the claims I decided not to make.
