# Gurobi stock-allocation extension

This optional junior operations-research exercise uses the published
`output/order_P19.csv` requests. It is separate from the original take-home
case result.

The model assumes only 90% of requested units are available. Integer decision
variables allocate units to store-item rows. A capacity constraint limits total
stock, while row-level constraints minimize the worst shortage rate. A second
objective uses as much capacity as possible.

```bash
pip install gurobipy
python optimization/allocate_with_gurobi.py --capacity-ratio 0.90
```

Gurobi licensing limits may apply. Change the ratio to compare illustrative
supply scenarios; do not treat the output as an implemented ordering policy.
