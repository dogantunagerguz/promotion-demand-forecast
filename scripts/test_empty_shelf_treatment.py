"""Ruled-out check: does excluding empty-shelf days bias the lift because those are the high-demand days?
(1) Empty-shelf rate by weekday and by format, normal vs promotion days.
(2) On promotion days: full-shelf mean sales vs the opening stock (lower bound) of the days that emptied.
(3) The lift computed three ways on the same item x promotion x format events: all days (raw), empty days
    excluded, empty days filled from the same promotion's full-shelf store-days (demand rule).
Run: python test_empty_shelf_treatment.py <data_folder> <output_folder>"""
import os
import numpy as np, pandas as pd
import forecast_p19 as F

df, promo = F.df, F.promo
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
t = df.groupby(["promo", "wd"])["shelf_empty"].mean().unstack("wd"); t.columns = days; t.index = ["normal day", "promotion day"]
print("Empty-shelf rate by weekday:\n", t.round(3).to_string())
prof = df[~df["promo"] & ~df["shelf_empty"]].groupby("wd")["units_sold"].mean(); prof.index = days
print("\nNormal days, full shelf, sales profile (mean = 1):\n", (prof / prof.mean()).round(2).to_string())
t2 = df.groupby(["promo", "format"])["shelf_empty"].mean().unstack("format"); t2.index = ["normal day", "promotion day"]
print("\nEmpty-shelf rate by format:\n", t2.round(3).to_string())
pg = df[df["promo"]]
print(f"\nPromotion days: full-shelf mean sales = {pg.loc[~pg['shelf_empty'], 'units_sold'].mean():.2f}; "
      f"emptied days' opening stock (lower bound) = {pg.loc[pg['shelf_empty'], 'stock_on_hand_open'].mean():.2f}")

def fill_rule(g):
    """empty day -> mean of the group's full-shelf days with sales >= that day's opening stock; else the stock itself"""
    full = g.loc[~g["shelf_empty"], "units_sold"].to_numpy()
    out = g["units_sold"].to_numpy().astype(float)
    for i, (e, s) in enumerate(zip(g["shelf_empty"].to_numpy(), g["stock_on_hand_open"].to_numpy())):
        if e:
            u = full[full >= s]; out[i] = u.mean() if len(u) else s
    return out

rows = []
for p in promo.itertuples():
    for fmt in [x.strip() for x in p.formats.split(",")]:
        m = (df["item_id"] == p.item_id) & (df["format"] == fmt)
        pre = df[m & df["date"].between(p.start_date - pd.Timedelta(days=21), p.start_date - pd.Timedelta(days=1))]
        week = df[m & df["date"].between(p.start_date, p.end_date)]
        if len(week) == 0 or len(pre) == 0:
            continue
        pre_f = np.concatenate([fill_rule(g) for _, g in pre.groupby("store_id")])   # before: per store-item
        week_f = fill_rule(week)                                                     # promotion week: per item-promotion-format
        pre_x, week_x = pre.loc[~pre["shelf_empty"], "units_sold"], week.loc[~week["shelf_empty"], "units_sold"]
        rows.append(dict(promo_id=p.promo_id, item_id=p.item_id, format=fmt, discount=p.discount,
                         empty_rate_week=week["shelf_empty"].mean(),
                         raw=week["units_sold"].mean() / pre["units_sold"].mean() if pre["units_sold"].mean() > 0 else np.nan,
                         excluded=week_x.mean() / pre_x.mean() if len(week_x) and len(pre_x) and pre_x.mean() > 0 else np.nan,
                         filled=week_f.mean() / pre_f.mean() if pre_f.mean() > 0 else np.nan))
lc = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).dropna()
print(f"\nLift three ways, item x promotion x format, n = {len(lc)}")
print(lc.groupby("format")[["raw", "excluded", "filled"]].mean().round(2).to_string())
lc["empty_group"] = pd.cut(lc["empty_rate_week"], [0, 0.1, 0.25, 0.5, 1.0], include_lowest=True)
print("\nBy the share of empty-shelf store-days in the promotion week:")
print(lc.groupby("empty_group", observed=True)[["raw", "excluded", "filled"]].agg(["mean", "count"]).round(2).to_string())
r = lc["filled"] / lc["excluded"]
print(f"\nfilled / excluded per event: median {r.median():.2f}; events > +10 %: {(r > 1.1).sum()}, < -10 %: {(r < 0.9).sum()}")
lc.to_csv(os.path.join(F.OUT, "lift_three_ways.csv"), index=False)
