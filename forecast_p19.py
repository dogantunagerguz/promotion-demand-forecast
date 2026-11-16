"""
P19 promotion forecast — single-file pipeline.

Run:  python forecast_p19.py <data_folder> <output_folder>
  data_folder must contain: daily_store_item.csv.gz (or .parquet), stores.csv, items.csv,
  promo_calendar.csv, promo_plan_next.csv

Steps
  1. Load data and flag store-days: empty shelf, promotion day, post-promotion day (1-14 days after),
     "category neighbour" (same category, same week, same format, not promoted).
  2. Baseline per store-item: 8 weeks before the forecast origin; promotion days, empty-shelf days and
     post-promotion days are excluded; mean of the remaining days x the store's weekday profile.
  3. Lift per format x category cell: in past promotions, sales on full-shelf store-days in the promotion week
     divided by the baseline on exactly the same store-days (sum / sum). Fallback with thin support:
     category -> format -> chain. A within-item discount slope adjusts the cell lift to the planned discount.
  4. Post-promotion factors (weeks +1 and +2) and category-neighbour factors, measured on history.
  5. P19 forecast for 4-24 August 2025 -> forecast_P19.csv
  6. Backtest P07-P18: the same method applied at each promotion's own origin; demand/forecast ratios give
     the calibration factor, the 80 % interval and the store-item error distribution.
  7. Bonus: order_P19.csv (lost sale 1.00, leftover 0.30 -> 77th percentile of demand).
"""
import sys, glob, os
import numpy as np, pandas as pd

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = sys.argv[2] if len(sys.argv) > 2 else "output"
os.makedirs(OUT, exist_ok=True)

def f(name):                      # the data folder may hold "<hash>-name" or "name"
    hits = glob.glob(os.path.join(DATA, f"*{name}"))
    assert hits, f"{name} not found in {DATA}"
    return hits[0]

# ============================================================== 1. DATA AND FLAGS
stores = pd.read_csv(f("stores.csv"))
items = pd.read_csv(f("items.csv"))
promo = pd.read_csv(f("promo_calendar.csv"), parse_dates=["start_date", "end_date"])
plan = pd.read_csv(f("promo_plan_next.csv"), parse_dates=["start_date", "end_date"])

daily_pkl = os.path.join(OUT, "daily.pkl")            # cache: the first run converts the csv.gz once
if os.path.exists(daily_pkl):
    df = pd.read_pickle(daily_pkl)
else:
    try:
        df = pd.read_parquet(f("daily_store_item.parquet"))
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        df = pd.read_csv(f("daily_store_item.csv.gz"), parse_dates=["date"])
    df.to_pickle(daily_pkl)
df = df.merge(stores[["store_id", "format"]], on="store_id").merge(items[["item_id", "category_id"]], on="item_id")
df["wd"] = df["date"].dt.weekday                                   # 0 = Monday
# Empty-shelf day: everything on the shelf was sold (opening stock 0 included).
# Sales on such a day are a lower bound on demand, not demand itself.
df["shelf_empty"] = df["units_sold"] >= df["stock_on_hand_open"]

def promo_store_days(tbl, start_off=0, end_off=0):
    """Expand a promotion table into (item, format, date) rows. start_off/end_off shift the window
    (e.g. start_off=7, end_off=14 -> from the day after the promotion ends to 14 days after it)."""
    rows = []
    for p in tbl.itertuples():
        for fmt in [x.strip() for x in p.formats.split(",")]:
            for d in pd.date_range(p.start_date + pd.Timedelta(days=start_off), p.end_date + pd.Timedelta(days=end_off)):
                rows.append((p.item_id, fmt, d, p.promo_id, p.discount, (d - p.end_date).days))
    return pd.DataFrame(rows, columns=["item_id", "format", "date", "promo_id", "discount", "days_after"])

KEY = ["item_id", "format", "date"]
pw = promo_store_days(promo)                                       # promotion days
df = df.merge(pw[KEY + ["promo_id"]], on=KEY, how="left")
df["promo"] = df["promo_id"].notna()
post = promo_store_days(promo, start_off=7, end_off=14).rename(columns={"promo_id": "post_promo_id"})
df = df.merge(post[KEY + ["post_promo_id", "days_after"]], on=KEY, how="left")   # days 1..14 after a promotion
df["post"] = df["post_promo_id"].notna()
cat_of = items.set_index("item_id")["category_id"]
pw["category_id"] = pw["item_id"].map(cat_of)
neigh = (pw.groupby(["category_id", "format", "date"])["promo_id"].first().reset_index()
           .rename(columns={"promo_id": "neigh_promo_id"}))
df = df.merge(neigh, on=["category_id", "format", "date"], how="left")
df["neighbour"] = df["neigh_promo_id"].notna() & ~df["promo"]       # same category and week, but not promoted

# ============================================================== 2. BASELINE
def baseline(df, origin, weeks=8, drop_post=False):
    """Store-item baseline and store weekday profile from the `weeks` weeks before `origin`.
    Excluded days: promotion days, empty-shelf days and (optionally) the 14 days after a promotion.
    Returns b (store_id, item_id -> daily mean, number of kept days) and prof (store_id, wd -> factor)."""
    start = origin - pd.Timedelta(days=7 * weeks)
    w = df[(df["date"] >= start) & (df["date"] < origin)]
    keep = w[~w["promo"] & ~w["shelf_empty"]]
    if drop_post:
        keep = keep[~keep["post"]]
    b = keep.groupby(["store_id", "item_id"])["units_sold"].agg(b="mean", n_kept="size")
    all_series = w[["store_id", "item_id"]].drop_duplicates().set_index(["store_id", "item_id"])
    b = all_series.join(b).fillna({"b": 0.0, "n_kept": 0})       # a series with no kept day gets b = 0
    prof = keep.groupby(["store_id", "wd"])["units_sold"].mean().unstack("wd")
    prof = prof.div(prof.mean(axis=1), axis=0).stack().rename("prof").reset_index()   # mean weekday = 1
    return b.reset_index(), prof

def daily_base(rows, b, prof):
    """rows with store_id, item_id, wd -> daily baseline = b x weekday factor."""
    x = rows.merge(b, on=["store_id", "item_id"], how="left").merge(prof, on=["store_id", "wd"], how="left")
    x["base_day"] = x["b"].fillna(0) * x["prof"].fillna(1)
    return x

# ============================================================== 3-4. HISTORICAL PROMOTION RECORDS
def promo_records(df, promo, drop_post):
    """For every past promotion, with a baseline rebuilt at that promotion's own start date:
       - promotion week, promoted items, full-shelf store-days: sales and baseline sums      (lift)
       - days 1-7 and 8-14 after the promotion, same items: sales and baseline sums          (post factors)
       - promotion week, same category, not promoted, full-shelf: sales and baseline sums    (neighbour factor)"""
    lift_recs, post_recs, neigh_recs = [], [], []
    for pid, grp in promo.groupby("promo_id"):
        start, end = grp["start_date"].iloc[0], grp["end_date"].iloc[0]
        b, prof = baseline(df, start, drop_post=drop_post)
        wk = df[(df["date"] >= start) & (df["date"] <= end) & ~df["shelf_empty"]]
        wk = daily_base(wk, b, prof)
        pr = wk[wk["promo_id"] == pid]
        for (it, fm), g in pr.groupby(["item_id", "format"]):
            lift_recs.append(dict(promo_id=pid, item_id=it, format=fm, category_id=cat_of[it],
                                  discount=grp.loc[grp["item_id"] == it, "discount"].iloc[0],
                                  num=g["units_sold"].sum(), den=g["base_day"].sum(), n_days=len(g)))
        nb = wk[(wk["neigh_promo_id"] == pid) & wk["neighbour"]]
        for (ct, fm), g in nb.groupby(["category_id", "format"]):
            neigh_recs.append(dict(promo_id=pid, category_id=ct, format=fm,
                                   num=g["units_sold"].sum(), den=g["base_day"].sum(), n_days=len(g)))
        ps = df[(df["post_promo_id"] == pid) & ~df["shelf_empty"]]
        ps = daily_base(ps, b, prof)
        ps["week_after"] = np.where(ps["days_after"] <= 7, 1, 2)
        for (it, fm, wa), g in ps.groupby(["item_id", "format", "week_after"]):
            post_recs.append(dict(promo_id=pid, item_id=it, format=fm, category_id=cat_of[it], week_after=wa,
                                  num=g["units_sold"].sum(), den=g["base_day"].sum(), n_days=len(g)))
    return pd.DataFrame(lift_recs), pd.DataFrame(post_recs), pd.DataFrame(neigh_recs)

def discount_slope(r, min_pairs=20):
    """Within-item test: same item, same format, two promotions at different discounts.
    Pairs' log-lift difference / discount difference -> how much a 10-point deeper discount multiplies the lift.
    Returns 1.0 (no effect) when fewer than `min_pairs` pairs exist."""
    import itertools
    rr = r[(r["den"] > 0) & (r["num"] > 0)].copy(); rr["L"] = rr["num"] / rr["den"]
    dl, dd = [], []
    for _, g in rr.groupby(["item_id", "format"]):
        for a, b in itertools.combinations(g.itertuples(), 2):
            if a.discount != b.discount:
                hi, lo = (a, b) if a.discount > b.discount else (b, a)
                dl.append(np.log(hi.L / lo.L)); dd.append(hi.discount - lo.discount)
    if len(dl) < min_pairs:
        return 1.0, len(dl)
    return float(np.exp(sum(dl) / sum(dd) * 0.10)), len(dl)

def lift_tables(recs, as_of, min_n=3):
    """Cell lifts (sum / sum) from promotions that started before `as_of`, with the number of item-promotions (n)
    and the baseline-weighted mean discount of each cell, plus the discount slope."""
    r = recs[recs["promo_id"].isin(promo.loc[promo["start_date"] < as_of, "promo_id"])]
    def cell(keys):
        g = r.assign(dw=r["discount"] * r["den"]).groupby(keys).agg(num=("num", "sum"), den=("den", "sum"), n=("promo_id", "size"), dw=("dw", "sum"))
        g["L"] = g["num"] / g["den"]; g["d_mean"] = g["dw"] / g["den"]
        return g.drop(columns="dw")
    chain = r["num"].sum() / r["den"].sum(); d_chain = (r["discount"] * r["den"]).sum() / r["den"].sum()
    slope, n_pairs = discount_slope(r)
    return dict(fc=cell(["format", "category_id"]), c=cell(["category_id"]), f=cell(["format"]), chain=chain, d_chain=d_chain,
                min_n=min_n, slope=slope, n_pairs=n_pairs)

def pick_lift(T, fmt, cat, discount):
    """Cascade: format x category -> category -> format -> chain (first level with >= min_n item-promotions).
    The chosen lift is adjusted for the gap between the plan's discount and the cell's mean discount:
    L x slope ** ((discount - d_mean) / 0.10). Returns (adjusted lift, level, n, raw lift, cell mean discount)."""
    for key, name in [((fmt, cat), "format x category"), (cat, "category"), (fmt, "format")]:
        tbl = T["fc"] if name == "format x category" else T["c"] if name == "category" else T["f"]
        if key in tbl.index and tbl.loc[key, "n"] >= T["min_n"]:
            L, d0, n = float(tbl.loc[key, "L"]), float(tbl.loc[key, "d_mean"]), int(tbl.loc[key, "n"])
            break
    else:
        L, d0, n, name = float(T["chain"]), float(T["d_chain"]), 0, "chain"
    return L * T["slope"] ** ((discount - d0) / 0.10), name, n, L, d0

# ============================================================== 5. FORECAST (same function for P19 and the backtest)
def forecast(df, plan_tbl, origin, horizon_start, horizon_end, recs, post_recs, neigh_recs, drop_post):
    """Forecast for `plan_tbl` prepared at `origin`, using only history before `origin`.
    Returns the daily grid, the lift choices per item x format, the factors used, and the baseline table."""
    b, prof = baseline(df, origin, drop_post=drop_post)
    T = lift_tables(recs, origin)
    hist = promo.loc[promo["start_date"] < origin, "promo_id"]
    pr = post_recs[post_recs["promo_id"].isin(hist)].groupby("week_after").agg(num=("num", "sum"), den=("den", "sum"))
    post_f = (pr["num"] / pr["den"]).to_dict()                       # {1: factor week +1, 2: factor week +2}
    nr = neigh_recs[neigh_recs["promo_id"].isin(hist)]
    neigh_all = nr["num"].sum() / nr["den"].sum()                    # chain-wide neighbour factor
    nc = nr.groupby("category_id").agg(num=("num", "sum"), den=("den", "sum"), n=("promo_id", "nunique"))
    neigh_cat = {c: (row["num"] / row["den"] if row["n"] >= 3 else neigh_all) for c, row in nc.iterrows()}
    series = df[["store_id", "item_id", "format", "category_id"]].drop_duplicates()
    days = pd.DataFrame({"date": pd.date_range(horizon_start, horizon_end)})
    grid = series.merge(days, how="cross")
    grid["wd"] = grid["date"].dt.weekday
    grid = daily_base(grid, b, prof)
    pdays = promo_store_days(plan_tbl)
    grid = grid.merge(pdays[KEY + ["promo_id"]].rename(columns={"promo_id": "plan_promo"}), on=KEY, how="left")
    pst = promo_store_days(plan_tbl, start_off=7, end_off=14)
    pst["week_after"] = np.where(pst["days_after"] <= 7, 1, 2)
    grid = grid.merge(pst[KEY + ["week_after"]], on=KEY, how="left")
    pdays["category_id"] = pdays["item_id"].map(cat_of)
    pn = pdays.groupby(["category_id", "format", "date"]).size().rename("plan_neigh").reset_index()
    grid = grid.merge(pn, on=["category_id", "format", "date"], how="left")
    choices, lifts = [], {}
    disc_of = plan_tbl.set_index("item_id")["discount"]
    for it in plan_tbl["item_id"].unique():
        for fmt in ["Hyper", "Super", "Express"]:
            L, lvl, n, L0, d0 = pick_lift(T, fmt, cat_of[it], disc_of[it])
            lifts[(it, fmt)] = L
            choices.append(dict(item_id=it, category_id=cat_of[it], format=fmt, plan_discount=disc_of[it],
                                cell_mean_discount=round(d0, 3), cell_lift=round(L0, 3), lift_used=round(L, 3),
                                level=lvl, n_item_promos=n, slope_per_10pts=round(T["slope"], 3), n_pairs=T["n_pairs"]))
    grid["lift"] = 1.0
    m = grid["plan_promo"].notna()
    grid.loc[m, "lift"] = [lifts[(i, f)] for i, f in zip(grid.loc[m, "item_id"], grid.loc[m, "format"])]
    grid["post_f"] = grid["week_after"].map(post_f).fillna(1.0)
    is_neigh = grid["plan_neigh"].notna() & grid["plan_promo"].isna()
    grid["neigh_f"] = np.where(is_neigh, grid["category_id"].map(neigh_cat).fillna(neigh_all), 1.0)
    grid["forecast"] = grid["base_day"] * grid["lift"] * grid["post_f"] * grid["neigh_f"]
    return grid, pd.DataFrame(choices), dict(post=post_f, neigh_all=neigh_all, neigh_cat=neigh_cat), b

def fill_demand(a):
    """Demand on the promotion week: full-shelf days keep their sales; an empty-shelf day gets the mean of the
    same item-promotion-format's full-shelf store-days whose sales are >= that day's opening stock
    (the shelf emptied, so demand was at least the opening stock); if none exists, the opening stock itself."""
    def fill(gr):
        full = gr.loc[~gr["shelf_empty"], "units_sold"].to_numpy()
        d = gr["units_sold"].to_numpy().astype(float)
        for i, (e, s) in enumerate(zip(gr["shelf_empty"].to_numpy(), gr["stock_on_hand_open"].to_numpy())):
            if e:
                u = full[full >= s]; d[i] = u.mean() if len(u) else s
        return pd.Series(d, index=gr.index)
    cols = ["units_sold", "shelf_empty", "stock_on_hand_open"]        # non-grouping columns only (avoids a pandas warning)
    return a.groupby(["item_id", "format"], group_keys=False)[cols].apply(fill)

# ============================================================== RUN
if __name__ == "__main__":
    recs0, post0, neigh0 = promo_records(df, promo, drop_post=False)
    pr = post0.groupby("week_after").agg(num=("num", "sum"), den=("den", "sum")); pr["factor"] = pr["num"] / pr["den"]
    print("Post-promotion factors (all history):\n", pr.round(3).to_string())
    DROP_POST = bool((pr["factor"] < 0.97).any())      # a clear post-promotion dip -> exclude those days from baselines too
    print("Post-promotion days excluded from baselines:", DROP_POST)
    recs, post_recs, neigh_recs = (recs0, post0, neigh0) if not DROP_POST else promo_records(df, promo, drop_post=True)
    recs.to_csv(os.path.join(OUT, "lift_records.csv"), index=False)
    nc = neigh_recs.groupby("category_id").agg(num=("num", "sum"), den=("den", "sum"), n_promos=("promo_id", "nunique"))
    nc["factor"] = (nc["num"] / nc["den"]).round(3)
    nc.to_csv(os.path.join(OUT, "neighbour_factor_by_category.csv"))
    print("Category-neighbour factor by category:\n", nc.to_string())
    pf = post_recs.groupby(["week_after", "format"]).agg(num=("num", "sum"), den=("den", "sum")); pf["factor"] = (pf["num"] / pf["den"]).round(3)
    pf.to_csv(os.path.join(OUT, "post_promotion_factors.csv"))

    # --- P19
    ORIGIN, H0, H1 = pd.Timestamp("2025-07-14"), pd.Timestamp("2025-08-04"), pd.Timestamp("2025-08-24")
    grid, choices, fac, b19 = forecast(df, plan, ORIGIN, H0, H1, recs, post_recs, neigh_recs, DROP_POST)
    choices.to_csv(os.path.join(OUT, "P19_lift_choices.csv"), index=False)
    T19 = lift_tables(recs, ORIGIN)
    T19["fc"].reset_index().round(3).to_csv(os.path.join(OUT, "lift_cells_format_category.csv"), index=False)
    T19["c"].reset_index().round(3).to_csv(os.path.join(OUT, "lift_cells_category.csv"), index=False)
    print("\nFormat lifts:\n", T19["f"].round(3).to_string(), "\nChain:", round(T19["chain"], 3),
          "| discount slope per 10 pts:", round(T19["slope"], 3), "from", T19["n_pairs"], "pairs")
    print("\nP19 lift levels used:\n", choices["level"].value_counts().to_string())
    wk = grid[grid["plan_promo"].notna() & grid["date"].between(H0, pd.Timestamp("2025-08-10"))]
    print(f"\nP19 promotion week, promoted items, raw forecast: {wk['forecast'].sum():,.0f} units")

    # --- 6. BACKTEST P07-P18
    bt_rows, bt_si = [], []
    for pid, grp in promo[promo["promo_id"] >= "P07"].groupby("promo_id"):
        start, end = grp["start_date"].iloc[0], grp["end_date"].iloc[0]
        g, _, _, _ = forecast(df, grp, start - pd.Timedelta(days=21), start, end, recs, post_recs, neigh_recs, DROP_POST)
        g = g[g["plan_promo"].notna()]
        act = df[df["promo_id"] == pid].copy()
        act["demand"] = fill_demand(act)
        cmp = g.merge(act[["store_id", "item_id", "date", "units_sold", "demand"]], on=["store_id", "item_id", "date"])
        si = cmp.groupby(["store_id", "item_id", "format"]).agg(pred=("forecast", "sum"), demand=("demand", "sum"), sold=("units_sold", "sum")).reset_index()
        si["promo_id"] = pid
        bt_si.append(si)
        bt_rows.append(dict(promo_id=pid, n_items=grp["item_id"].nunique(), pred=si["pred"].sum(), demand=si["demand"].sum(),
                            sold=si["sold"].sum(), error=si["demand"].sum() / si["pred"].sum() - 1))
    bt = pd.DataFrame(bt_rows); bt.to_csv(os.path.join(OUT, "backtest_promotions.csv"), index=False)
    bt_si = pd.concat(bt_si); bt_si.to_csv(os.path.join(OUT, "backtest_store_item.csv"), index=False)
    print("\nBacktest (promotion week totals, demand / forecast - 1):\n", bt.round(3).to_string(index=False))
    le = np.log1p(bt["error"]); mu, sd = le.mean(), le.std(ddof=1)
    cal = float(np.exp(mu))                                        # systematic gap measured in the backtest
    tot_raw = wk["forecast"].sum()
    print(f"\nLog-error mean {mu:.3f}, sd {sd:.3f} (n={len(bt)}) -> calibration factor {cal:.3f}")

    # --- P19 file: promoted items' promotion-week forecast x calibration
    m19 = grid["plan_promo"].notna()
    grid.loc[m19, "forecast"] = grid.loc[m19, "forecast"] * cal
    out = grid[["date", "store_id", "item_id", "forecast"]].sort_values(["date", "store_id", "item_id"])
    out["forecast"] = out["forecast"].round(3)
    out.to_csv(os.path.join(OUT, "forecast_P19.csv"), index=False)
    tot = tot_raw * cal

    # --- 80 % interval: backtest ratios for the share with precedent; added spread for the share without
    ratios = 1 + bt["error"]
    r_lo, r_hi = np.percentile(ratios, [10, 90])                   # central 80 % of demand / forecast ratios
    wk_items = wk.merge(plan[["item_id", "discount"]], on="item_id")
    outside = wk_items[(wk_items["category_id"] == 17) | (wk_items["discount"] >= 0.45)]["forecast"].sum()
    inside = tot_raw - outside
    fcl = T19["fc"][T19["fc"]["n"] >= 3]
    sd_cell = float(np.log(fcl["L"]).groupby(fcl.index.get_level_values("format")).std().mean())
    spread = 1.2816 * sd_cell                                      # +-16 %: spread of category lifts within a format
    lo = inside * r_lo + outside * cal * np.exp(-spread)
    hi = inside * r_hi + outside * cal * np.exp(spread)
    print(f"Backtest ratio range (central 80 %): {r_lo:.3f}-{r_hi:.3f}; share without precedent: {outside/tot_raw:.0%}; "
          f"cell-lift log-sd {sd_cell:.3f} (+-{np.exp(spread)-1:.0%})")
    print(f"P19 promotion week total (calibrated): {tot:,.0f}; 80 % interval: {lo:,.0f} - {hi:,.0f}  (raw {tot_raw:,.0f})")
    print("  by format:", wk.groupby("format")["forecast"].sum().mul(cal).round(0).to_dict())
    pd.DataFrame([dict(total_raw=tot_raw, calibration=cal, total=tot, interval_low=lo, interval_high=hi, backtest_n=len(bt),
                       ratio_p10=r_lo, ratio_p90=r_hi, share_without_precedent=outside / tot_raw, cell_lift_log_sd=sd_cell)]
                 ).round(4).to_csv(os.path.join(OUT, "P19_total_and_interval.csv"), index=False)

    # --- 7. ORDER: 77th percentile of the store-item demand/forecast ratio, by format
    ok = bt_si[bt_si["pred"] > 0].copy(); ok["r"] = ok["demand"] / ok["pred"]
    q = ok.groupby("format")["r"].quantile(1 / 1.3).to_dict()
    print("\nStore-item demand/forecast ratio, 77th percentile by format:", {k: round(v, 3) for k, v in q.items()},
          "| median:", ok.groupby("format")["r"].median().round(3).to_dict())
    order = wk.groupby(["store_id", "item_id", "format"])["forecast"].sum().reset_index()      # raw weekly forecast
    order["units"] = np.ceil(order["forecast"] * order["format"].map(q)).astype(int)
    order[["store_id", "item_id", "units"]].to_csv(os.path.join(OUT, "order_P19.csv"), index=False)
    print(f"Order total: {order['units'].sum():,} units (calibrated forecast total {tot:,.0f})")
