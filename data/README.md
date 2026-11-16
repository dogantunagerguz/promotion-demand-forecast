# Data (not included)

The data belongs to the company that set the case. The pipeline expects these files in this folder:

| File | Columns | Notes |
| --- | --- | --- |
| `daily_store_item.csv.gz` (or `.parquet`) | date, store_id, item_id, units_sold, stock_on_hand_open | One row per store, item and day; `stock_on_hand_open` is the shelf stock at opening, after that morning's delivery |
| `stores.csv` | store_id, format, size_sqm, remodeled_2024 | 30 stores: Hyper, Super, Express |
| `items.csv` | item_id, category_id, department | 180 items, 18 categories, 4 departments |
| `promo_calendar.csv` | promo_id, item_id, start_date, end_date, discount, formats | Past promotions (P01–P18) |
| `promo_plan_next.csv` | same columns | The plan to forecast (P19) |
| `our_forecast_P18.csv` | date, store_id, item_id, baseline, lift_applied, forecast | The company's own forecast for P18, used in the comparison |
