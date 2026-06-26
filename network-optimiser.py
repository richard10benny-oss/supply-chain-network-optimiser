"""
Supply Chain Network Design Optimizer
=====================================
Capacitated facility location as a mixed-integer linear program (MILP).

Decision: which candidate distribution centers (DCs) to open, and how to
route product flow from open DCs to demand regions, at minimum total cost
(fixed cost of opening DCs + variable transport cost).

Solver: CBC (bundled with PuLP).

Run:
    pip install pulp
    python network_optimizer.py
"""

import math
import pulp


# ----------------------------------------------------------------------
# 1. DATA
# Replace this synthetic block with real candidate DCs and demand regions.
# Coordinates are arbitrary planar (x, y); distance is Euclidean here.
# ----------------------------------------------------------------------

# Candidate distribution centers: id -> fixed opening cost, capacity, location
dcs = {
    "DC1": {"x": 10, "y": 60, "fixed": 1800, "cap": 9000},
    "DC2": {"x": 35, "y": 30, "fixed": 1500, "cap": 8000},
    "DC3": {"x": 60, "y": 70, "fixed": 2000, "cap": 12000},
    "DC4": {"x": 75, "y": 25, "fixed": 1600, "cap": 7000},
    "DC5": {"x": 50, "y": 50, "fixed": 2200, "cap": 15000},
}

# Demand regions: id -> demand units, location
regions = {
    "R1": {"x": 12, "y": 55, "demand": 2200},
    "R2": {"x": 30, "y": 40, "demand": 1800},
    "R3": {"x": 58, "y": 65, "demand": 2600},
    "R4": {"x": 80, "y": 30, "demand": 1500},
    "R5": {"x": 45, "y": 20, "demand": 2000},
    "R6": {"x": 65, "y": 50, "demand": 2400},
    "R7": {"x": 20, "y": 75, "demand": 1300},
    "R8": {"x": 70, "y": 80, "demand": 1700},
}

COST_PER_UNIT_DISTANCE = 1.0   # transport cost per unit of demand per unit distance
MAX_SERVICE_DISTANCE = 60.0    # a DC cannot serve a region farther than this


def distance(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


# per-unit transport cost on each lane, and which lanes are within service range
transport_cost = {}
allowed = {}
for i, ri in regions.items():
    for j, dj in dcs.items():
        d = distance(ri, dj)
        transport_cost[(i, j)] = COST_PER_UNIT_DISTANCE * d
        allowed[(i, j)] = d <= MAX_SERVICE_DISTANCE


# ----------------------------------------------------------------------
# 2. MODEL
# ----------------------------------------------------------------------

def build_and_solve(demand_multiplier=1.0, verbose=True):
    demand = {i: regions[i]["demand"] * demand_multiplier for i in regions}

    model = pulp.LpProblem("network_design", pulp.LpMinimize)

    # y[j] = 1 if DC j is opened (binary)
    y = {j: pulp.LpVariable(f"open_{j}", cat="Binary") for j in dcs}

    # x[i, j] = units shipped from DC j to region i (continuous, allowed lanes only)
    x = {
        (i, j): pulp.LpVariable(f"flow_{i}_{j}", lowBound=0)
        for i in regions for j in dcs if allowed[(i, j)]
    }

    # Objective: fixed opening cost + variable transport cost
    model += (
        pulp.lpSum(dcs[j]["fixed"] * y[j] for j in dcs)
        + pulp.lpSum(transport_cost[(i, j)] * x[(i, j)] for (i, j) in x)
    )

    # Demand satisfaction: every region's demand is fully met
    for i in regions:
        model += (
            pulp.lpSum(x[(i, j)] for j in dcs if (i, j) in x) == demand[i],
            f"demand_{i}",
        )

    # Capacity + linking: a DC ships only if open, and never beyond capacity
    for j in dcs:
        model += (
            pulp.lpSum(x[(i, j)] for i in regions if (i, j) in x)
            <= dcs[j]["cap"] * y[j],
            f"capacity_{j}",
        )

    model.solve(pulp.PULP_CBC_CMD(msg=0))

    status = pulp.LpStatus[model.status]
    total_cost = pulp.value(model.objective)
    opened = [j for j in dcs if y[j].value() > 0.5]

    if verbose:
        print(f"Status: {status}")
        print(f"Total cost: {total_cost:,.0f}")
        print(f"DCs opened ({len(opened)}): {', '.join(opened)}")
        print("Assignments:")
        for (i, j) in sorted(x):
            v = x[(i, j)].value()
            if v and v > 1e-6:
                print(f"  {i} served by {j}: {v:,.0f} units")

    return {"status": status, "cost": total_cost, "opened": opened}


# ----------------------------------------------------------------------
# 3. SENSITIVITY: how the optimal network shifts as demand grows
# ----------------------------------------------------------------------

def sensitivity():
    print("\nDemand sensitivity")
    print("-" * 48)
    print(f"{'multiplier':>10} {'cost':>12} {'opened':>8}  DCs")
    for m in [0.8, 1.0, 1.2, 1.5, 2.0]:
        r = build_and_solve(demand_multiplier=m, verbose=False)
        print(f"{m:>10.1f} {r['cost']:>12,.0f} {len(r['opened']):>8}  {', '.join(r['opened'])}")


if __name__ == "__main__":
    print("Base case")
    print("=" * 48)
    build_and_solve()
    sensitivity()
