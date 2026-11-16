"""
Part 2, belief 1: "Fast-selling items respond less to promotions than slow-selling items, so there is little
                   point promoting them."
Part 2, belief 2: "Stores remodeled in 2024 respond better to promotions than the other stores."

Data: output/lift_records.csv (item x promotion x format) and the daily data for store-level lifts.
Run: python test_beliefs_1_2.py <data_folder> <output_folder>  (same arguments as forecast_p19.py)
"""
import sys, os
import numpy as np, pandas as pd
from scipy import stats
import forecast_p19 as F

OUT = F.OUT
df, promo, stores = F.df, F.promo, F.stores

# ============================================================ BELIEF 1: fast vs slow items
r = pd.read_csv(os.path.join(OUT, "lift_records.csv"))
r = r[(r["num"] > 0) & (r["den"] > 0)].copy()
r["L"] = r["num"] / r["den"]
r["base_daily"] = r["den"] / r["n_days"]              # the item's daily baseline per store-day in that format = speed
r["speed"] = r.groupby("format")["base_daily"].transform(lambda s: pd.qcut(s, 4, labels=["Q1 slow", "Q2", "Q3", "Q4 fast"]))
r["extra_units"] = (r["num"] - r["den"]) / r["n_days"]  # extra units per store-day brought by the promotion
t = r.groupby(["format", "speed"], observed=True).agg(n=("L", "size"), base=("base_daily", "mean"),
                                                     mean_lift=("L", "mean"), median_lift=("L", "median"),
                                                     extra_units=("extra_units", "mean"))
print("Belief 1 - lift and extra units per store-day, by speed quartile within format:")
print(t.round(2).to_string())
print("\nSpearman correlation log(baseline) ~ log(lift), by format:")
for fm, g in r.groupby("format"):
    rho, p = stats.spearmanr(np.log(g["base_daily"]), np.log(g["L"]))
    print(f"  {fm:8s} n={len(g):3d}  rho={rho:+.3f}  p={p:.3g}")
t.round(3).to_csv(os.path.join(OUT, "belief1_speed_quartiles.csv"))

# ============================================================ BELIEF 2: remodeled stores
# Store x promotion lift (sum / sum over full-shelf store-days, baseline rebuilt at the promotion's start).
# No remodel dates are given, so: 2023 promotions = before, 2025 promotions = after, 2024 = transition.
rows = []
for pid, grp in promo.groupby("promo_id"):
    start, end = grp["start_date"].iloc[0], grp["end_date"].iloc[0]
    b, prof = F.baseline(df, start, drop_post=True)
    wk = df[(df["date"] >= start) & (df["date"] <= end) & ~df["shelf_empty"] & (df["promo_id"] == pid)]
    wk = F.daily_base(wk, b, prof)
    for sid, g in wk.groupby("store_id"):
        rows.append(dict(promo_id=pid, store_id=sid, num=g["units_sold"].sum(), den=g["base_day"].sum(), n_days=len(g)))
sl = pd.DataFrame(rows).merge(stores, on="store_id")
sl = sl[sl["den"] > 0]; sl["L"] = sl["num"] / sl["den"]
sl["period"] = np.where(sl["promo_id"] <= "P04", "2023 (before)", np.where(sl["promo_id"] >= "P15", "2025 (after)", "2024 (transition)"))
sl.to_csv(os.path.join(OUT, "belief2_store_lifts.csv"), index=False)

print("\nBelief 2 - store x promotion lift by remodel status (sum / sum, within format):")
tab = sl.groupby(["period", "format", "remodeled_2024"]).agg(n_store_promos=("L", "size"), num=("num", "sum"), den=("den", "sum"))
tab["lift"] = tab["num"] / tab["den"]; tab = tab.drop(columns=["num", "den"])
print(tab.round(2).to_string())
print("\n2025 promotions (after the remodel), within format, Mann-Whitney on store x promotion lifts:")
for fm, g in sl[sl["period"] == "2025 (after)"].groupby("format"):
    a, bb = g.loc[g["remodeled_2024"], "L"], g.loc[~g["remodeled_2024"], "L"]
    u, p = stats.mannwhitneyu(a, bb, alternative="two-sided")
    print(f"  {fm:8s} remodeled n={len(a):2d} median {a.median():.2f} | others n={len(bb):2d} median {bb.median():.2f} | p={p:.3f}")
ch = (sl[sl["period"] != "2024 (transition)"].groupby(["store_id", "format", "remodeled_2024", "period"])[["num", "den"]]
        .apply(lambda g: g["num"].sum() / g["den"].sum()).unstack("period"))
ch["change"] = np.log(ch["2025 (after)"] / ch["2023 (before)"])
print("\nSame store, 2023 -> 2025 change in log-lift (difference in differences):")
print(ch.groupby(["format", "remodeled_2024"])["change"].agg(["size", "mean"]).round(3).to_string())
a = ch.loc[ch.index.get_level_values("remodeled_2024"), "change"]; bb = ch.loc[~ch.index.get_level_values("remodeled_2024"), "change"]
u, p = stats.mannwhitneyu(a, bb, alternative="two-sided")
print(f"  remodeled n={len(a)} mean {a.mean():+.3f} | others n={len(bb)} mean {bb.mean():+.3f} | Mann-Whitney p={p:.3f}")
