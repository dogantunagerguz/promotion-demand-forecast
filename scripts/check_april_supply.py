"""Ruled-out check: was the April 2025 drop a demand drop or a supply problem?
Weekly opening stock, sales and empty-shelf rate for all store-items, spring 2025 vs the same weeks in 2024.
Run: python check_april_supply.py <data_folder> <output_folder>"""
import os
import pandas as pd
import forecast_p19 as F

df = F.df
def weekly(a, b):
    w = df[(df["date"] >= a) & (df["date"] <= b)].copy()
    w["week"] = w["date"].dt.to_period("W-SUN").dt.start_time.dt.strftime("%d %b %Y")
    t = w.groupby("week", sort=False).agg(sales_per_store_item_day=("units_sold", "mean"),
                                           opening_stock=("stock_on_hand_open", "mean"),
                                           empty_shelf_rate=("shelf_empty", "mean"),
                                           zero_stock_rate=("stock_on_hand_open", lambda s: (s == 0).mean()))
    return t.round(3)
t25 = weekly("2025-03-03", "2025-06-15"); t24 = weekly("2024-03-04", "2024-06-16")
print("2025:\n", t25.to_string()); print("\n2024, same weeks:\n", t24.to_string())
# which categories were hit hardest in the four April weeks
w = df[(df["date"] >= "2025-04-07") & (df["date"] <= "2025-05-04")]
ref = df[(df["date"] >= "2025-03-10") & (df["date"] <= "2025-04-06")]
c = pd.DataFrame({"april_stock": w.groupby("category_id")["stock_on_hand_open"].mean(),
                  "march_stock": ref.groupby("category_id")["stock_on_hand_open"].mean(),
                  "april_empty_rate": w.groupby("category_id")["shelf_empty"].mean(),
                  "march_empty_rate": ref.groupby("category_id")["shelf_empty"].mean()})
c["stock_change"] = (c["april_stock"] / c["march_stock"] - 1).round(3)
print("\nBy category, 7 Apr-4 May vs 10 Mar-6 Apr:\n", c.round(3).sort_values("stock_change").to_string())
t25.to_csv(os.path.join(F.OUT, "april_weekly_2025.csv")); t24.to_csv(os.path.join(F.OUT, "april_weekly_2024.csv"))
c.round(3).to_csv(os.path.join(F.OUT, "april_by_category.csv"))
