# supply-chain-network-optimiser
# Supply Chain Network Design Optimizer

A mixed-integer linear program (MILP) that designs a distribution network: it
chooses which candidate distribution centers (DCs) to open and how to route
product flow from those DCs to demand regions, at minimum total cost.

Status: Ongoing. The core model runs and solves to optimality. Active work is
listed under Roadmap.

## Problem

Given candidate DC locations (each with a fixed opening cost and a capacity) and
demand regions (each with a known demand), decide:

1. which DCs to open, and
2. how many units to ship from each open DC to each region,

so total cost is minimized while all demand is met, no DC exceeds its capacity,
and no region is served by a DC beyond a maximum service distance.

## Formulation

Sets:
- j in DCs, candidate distribution centers
- i in Regions, demand regions

Decision variables:
- y_j in {0, 1}: 1 if DC j is opened, else 0 (binary)
- x_ij >= 0: units shipped from DC j to region i (continuous)

Parameters:
- f_j: fixed cost to open DC j
- cap_j: capacity of DC j
- d_i: demand of region i
- c_ij: per-unit transport cost from DC j to region i (distance based)
- Dmax: maximum allowed service distance (lanes beyond Dmax are removed)

Objective (minimize):

    sum_j f_j * y_j  +  sum_ij c_ij * x_ij

Subject to:
- Demand satisfaction:  sum_j x_ij = d_i           for every region i
- Capacity and linking: sum_i x_ij <= cap_j * y_j  for every DC j
- Service distance:     x_ij exists only when distance(i, j) <= Dmax
- Non-negativity:       x_ij >= 0
- Integrality:          y_j in {0, 1}

The capacity constraint also links flow to the open decision: if y_j = 0 the
right side is 0, so a closed DC ships nothing. The model is integer rather than
a plain LP because opening a DC is a discrete yes-or-no choice; relaxing y_j to
a fraction would allow a "partially open" DC, which has no meaning here.

## Run

    pip install pulp
    python network_optimizer.py

It solves the base case, prints the opened DCs and region assignments, then runs
a demand sensitivity sweep, all on the free CBC solver bundled with PuLP.

## Results

Total base demand slightly exceeds the largest single DC's capacity, so the
optimizer opens more than one DC and assigns each region to its cheapest
reachable open DC. The sensitivity sweep shows additional DCs opening as demand
scales. Paste your exact run output here.

## Data

The data block in the script is synthetic, with planar coordinates and Euclidean
distances, so it runs with zero setup. Swap in real candidate sites, capacities,
demands, and a real distance or cost matrix to make it concrete.

## Roadmap

- Replace synthetic data with a real or realistic dataset
- Add a single-source variant (each region served by exactly one DC)
- Add fixed lane costs and minimum-throughput constraints
- Visualize the chosen network on a map
- Compare scenarios side by side and report the main cost drivers
