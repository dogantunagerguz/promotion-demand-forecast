"""
Part 2, belief 3: "Discount depth barely matters. A 20% discount sells about as well as a 40% one."

Two tests on the same records (output/lift_records.csv, produced by forecast_p19.py; unit: item x promotion x format;
num = promotion-week sales on full-shelf store-days, den = baseline on the same store-days, lift = num / den):

  A. Across items: group promotions by discount, average the lifts. Cannot separate the discount from which items
     received deep discounts.
  B. Within item: same item, same format, two promotions at different discounts = one pair. Compare the pair's
     lifts. The item is held fixed, so "which item got the deep discount" no longer matters.

Run: python test_discount_depth.py output/lift_records.csv
"""
import sys, itertools, os
import numpy as np, pandas as pd
from math import comb

path = sys.argv[1] if len(sys.argv) > 1 else "output/lift_records.csv"
r = pd.read_csv(path)
r = r[(r["num"] > 0) & (r["den"] > 0)].copy()
r["L"] = r["num"] / r["den"]
print(f"Records: {len(r)} item x promotion x format, {r['item_id'].nunique()} items, {r['promo_id'].nunique()} promotions")

# ---------------------------------------------------------------- A. across items
a = r.groupby("discount").agg(n=("L", "size"), mean_lift=("L", "mean"), num=("num", "sum"), den=("den", "sum"))
a["sum_over_sum_lift"] = a["num"] / a["den"]
a["promotions"] = r.groupby("discount")["promo_id"].agg(lambda s: ",".join(sorted(set(s))))
print("\nA. Across items, by discount:")
print(a[["n", "mean_lift", "sum_over_sum_lift", "promotions"]].round(2).to_string())
print("   -> flat between 15% and 35%; the 10% row is P18 only, the 40% row is P03 (2 items) and P18.")

# ---------------------------------------------------------------- B. within-item pairs
rows = []
for (it, fm), g in r.groupby(["item_id", "format"]):
    for x, y in itertools.combinations(g.itertuples(), 2):
        if x.discount == y.discount:
            continue
        hi, lo = (x, y) if x.discount > y.discount else (y, x)
        rows.append(dict(item_id=it, format=fm, shallow=lo.discount, deep=hi.discount, gap=hi.discount - lo.discount,
                         log_ratio=np.log(hi.L / lo.L), p_shallow=lo.promo_id, p_deep=hi.promo_id))
p = pd.DataFrame(rows)
n_pairs, n_items = len(p), p["item_id"].nunique()
ratio = float(np.exp(p["log_ratio"].mean()))
slope10 = float(np.exp(p["log_ratio"].sum() / p["gap"].sum() * 0.10))
share_pos = float((p["log_ratio"] > 0).mean())
print(f"\nB. Within item: {n_pairs} pairs, {n_items} items")
print(f"   typical deep/shallow lift ratio: {ratio:.3f}; a 10-point deeper discount multiplies the lift by {slope10:.3f}; "
      f"deep > shallow in {share_pos:.0%} of pairs")
p["gap_group"] = pd.cut(p["gap"], [0, 0.05, 0.10, 0.15, 0.30], labels=["<=5 pts", "6-10", "11-15", "16-30"])
print(p.groupby("gap_group", observed=True).agg(n=("log_ratio", "size"),
      deep_over_shallow=("log_ratio", lambda s: round(float(np.exp(s.mean())), 3))).to_string())
k, n = int((p["log_ratio"] > 0).sum()), n_pairs
p_value = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
print(f"   sign test: deep > shallow in {k}/{n} pairs, H0 = 50%, one-sided p = {p_value:.2e}")
q = p[(p["p_deep"] != "P18") & (p["p_shallow"] != "P18")]
print(f"   excluding P18: {len(q)} pairs, ratio {np.exp(q['log_ratio'].mean()):.3f}, per 10 pts x{np.exp(q['log_ratio'].sum()/q['gap'].sum()*0.10):.3f}")
print("   per-10-pt effect by format:", {f: round(float(np.exp(g['log_ratio'].sum() / g['gap'].sum() * 0.10)), 3) for f, g in p.groupby("format")})
p.to_csv(os.path.join(os.path.dirname(path) or ".", "discount_pairs.csv"), index=False)
