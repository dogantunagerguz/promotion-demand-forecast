"""Illustrative stock-allocation model built from the published P19 order file.

This is a junior operations-research extension, not part of the original case
result. It allocates a limited percentage of requested units while minimizing
the worst row-level shortage rate.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB


def read_requests(path: Path) -> list[dict[str, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [
            {key: int(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]
    if not rows or any(row["units"] <= 0 for row in rows):
        raise ValueError("Expected positive unit requests.")
    return rows


def optimize(rows: list[dict[str, int]], capacity_ratio: float) -> list[dict[str, int]]:
    if not 0 < capacity_ratio <= 1:
        raise ValueError("capacity_ratio must be in (0, 1].")

    model = gp.Model("promotion_stock_allocation")
    model.Params.OutputFlag = 0
    allocation = {
        i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=row["units"], name=f"alloc_{i}")
        for i, row in enumerate(rows)
    }
    worst_shortage_rate = model.addVar(lb=0, ub=1, name="worst_shortage_rate")

    total_request = sum(row["units"] for row in rows)
    capacity = math.floor(total_request * capacity_ratio)
    model.addConstr(gp.quicksum(allocation.values()) <= capacity, name="capacity")
    for i, row in enumerate(rows):
        model.addConstr(
            row["units"] - allocation[i] <= worst_shortage_rate * row["units"],
            name=f"fair_shortage_{i}",
        )

    model.setObjectiveN(worst_shortage_rate, index=0, priority=2, name="fairness")
    model.setObjectiveN(
        -gp.quicksum(allocation.values()), index=1, priority=1, name="use_capacity"
    )
    model.optimize()
    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Gurobi ended with status {model.Status}")

    return [
        {
            **row,
            "allocated_units": int(round(allocation[i].X)),
            "shortage_units": row["units"] - int(round(allocation[i].X)),
        }
        for i, row in enumerate(rows)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("output/order_P19.csv"))
    parser.add_argument("--output", type=Path, default=Path("output/gurobi_allocation.csv"))
    parser.add_argument("--capacity-ratio", type=float, default=0.90)
    args = parser.parse_args()

    result = optimize(read_requests(args.input), args.capacity_ratio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=result[0].keys())
        writer.writeheader()
        writer.writerows(result)
    print(
        f"Allocated {sum(r['allocated_units'] for r in result):,} of "
        f"{sum(r['units'] for r in result):,} requested units."
    )


if __name__ == "__main__":
    main()
