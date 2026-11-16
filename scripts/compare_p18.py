"""Part 1 evidence: the company's P18 forecast (our_forecast_P18.csv) vs our method run at the same origin
(26 May 2025) vs actuals, by segment, format, day and category.
Run: python compare_p18.py <data_folder> <output_folder>"""
import sys, os
import numpy as np, pandas as pd
import forecast_p19 as F

OUT = F.OUT
df, promo = F.df, F.promo
p18 = promo[promo["promo_id"] == "P18"]
ORIGIN, H0, H1 = pd.Timestamp("2025-05-26"), pd.Timestamp("2025-05-26"), pd.Timestamp("2025-07-06")
S, E = pd.Timestamp("2025-06-16"), pd.Timestamp("2025-06-22")
CAL = 1.074                                                   # calibration factor measured in the backtest

# our method at 26 May 2025 (only data before that date)
recs, post_recs, neigh_recs = F.promo_records(df, promo, drop_post=True)
g, choices, fac, _ = F.forecast(df, p18, ORIGIN, H0, H1, recs, post_recs, neigh_recs, True)
g.loc[g["plan_promo"].notna(), "forecast"] *= CAL
ours = g[["date", "store_id", "item_id", "forecast"]].rename(columns={"forecast": "ours"})

company = pd.read_csv(F.f("our_forecast_P18.csv"), parse_dates=["date"]).rename(columns={"forecast": "company"})

# actuals: sales; in the promotion week, empty-shelf days filled with the demand rule
act = df[(df["date"] >= H0) & (df["date"] <= H1)][["date", "store_id", "item_id", "format", "category_id",
                                                     "units_sold", "shelf_empty", "stock_on_hand_open", "promo_id"]].copy()
act["demand"] = act["units_sold"].astype(float)
m = act["promo_id"] == "P18"
act.loc[m, "demand"] = F.fill_demand(act[m])

x = (act.merge(company[["date", "store_id", "item_id", "company", "lift_applied"]], on=["date", "store_id", "item_id"])
        .merge(ours, on=["date", "store_id", "item_id"]))
p18_items = set(p18["item_id"]); p18_cats = set(F.cat_of[i] for i in p18_items)
def seg(r):
    if r["item_id"] in p18_items:
        if S <= r["date"] <= E: return "1 promoted item, promotion week"
        if E < r["date"] <= E + pd.Timedelta(days=14): return "2 promoted item, next 2 weeks"
        return "4 promoted item, other days"
    if r["category_id"] in p18_cats and S <= r["date"] <= E: return "3 same category, not promoted, promotion week"
    return "5 other items"
x["segment"] = x.apply(seg, axis=1)

def tbl(keys):
    t = x.groupby(keys).agg(sales=("units_sold", "sum"), demand=("demand", "sum"), company=("company", "sum"), ours=("ours", "sum"))
    for c in ["company", "ours"]:
        t[f"{c}/sales"] = t[c] / t["sales"]; t[f"{c}/demand"] = t[c] / t["demand"]
    return t.round(2)
t1 = tbl("segment"); print("By segment:\n", t1.to_string())
t2 = tbl(["segment", "format"]); print("\nBy segment x format:\n", t2.to_string())
w = x[x["segment"].str.startswith("1")]
t3 = w.groupby("date").agg(sales=("units_sold", "sum"), demand=("demand", "sum"), company=("company", "sum"), ours=("ours", "sum")).round(0)
print("\nPromotion week by day:\n", t3.to_string())
t4 = w.groupby("category_id").agg(sales=("units_sold", "sum"), demand=("demand", "sum"), company=("company", "sum"), ours=("ours", "sum"),
                                 company_lift=("lift_applied", "mean")).round(1)
t4["company/demand"] = (t4["company"] / t4["demand"]).round(2); t4["ours/demand"] = (t4["ours"] / t4["demand"]).round(2)
print("\nPromotion week by category:\n", t4.to_string())
oth = x[x["segment"] == "5 other items"]
t5 = oth.groupby("category_id").agg(sales=("units_sold", "sum"), company=("company", "sum"), ours=("ours", "sum"))
t5["company/sales"] = (t5["company"] / t5["sales"]).round(3); t5["ours/sales"] = (t5["ours"] / t5["sales"]).round(3)
print("\nOther items (baseline check) by category, forecast/sales:\n", t5[["sales", "company/sales", "ours/sales"]].to_string())
x["ae_c"] = (x["company"] - x["units_sold"]).abs(); x["ae_o"] = (x["ours"] - x["units_sold"]).abs()
print("\nAbsolute error vs sales, store-item-day: company", round(x["ae_c"].sum()), " ours", round(x["ae_o"].sum()))
for t, n in [(t1, "p18_segments.csv"), (t2, "p18_segments_format.csv"), (t3, "p18_days.csv"), (t4, "p18_categories.csv"), (t5, "p18_baseline_by_category.csv")]:
    t.to_csv(os.path.join(OUT, n))
