# Scenario 11 Simulation Failure Report

## Execution Summary

Attempted to run **Scenario 11: Sibiu Regional Crisis** using `snakemake` with the `pypsa-eur` environment.

**Command:**
```powershell
C:\Users\Administrator\.conda\envs\pypsa-eur\Scripts\snakemake.exe -call results/romania-adversarial-11-sibiu_regional_crisis/networks/base_s_10_elec_.nc --configfile config/adversarial/romania_adversarial_11_sibiu_regional_crisis.yaml
```

## Error Analysis

The simulation failed during the **`cluster_network`** job.

**Error Message:**
```
ValueError: Solver scip does not support quadratic problems.
```

**Reason:**
1. The clustering algorithm (`distribute_n_clusters_to_countries`) attempted to solve an optimization problem with a **quadratic objective function**.
2. The configured solver **HiGHS** does not support quadratic objectives (or is configured such that it reports it doesn't).
   > `INFO:__main__:The configured solver highs does not support quadratic objectives. Falling back to scip.`
3. The fallback solver **SCIP** (bundled with PyPSA/Linopy?) also reported that it does not support quadratic problems in this context.

## Workflow Logs

### 1. Initial Checks & GDAL Warnings
Multiple warnings about missing GDAL data were met. These are generally non-fatal warnings related to spatial data processing.
```text
Warning 3: Cannot find gdalvrt.xsd (GDAL_DATA is not defined)
Config file config/config.default.yaml is extended by additional config specified via the command line.
```

### 2. Successful Steps
The workflow successfully completed 9 of 21 steps, including:
- `build_shapes`
- `build_electricity_demand`
- `base_network` (building the raw network)
- `build_line_rating`
- `simplify_network` (simplifying topology)

### 3. Failure Step: `cluster_network`
This step attempts to aggregate the simplified network into 10 clusters (as defined in the scenario).

```text
[Mon Feb  9 13:12:44 2026]
localrule cluster_network:
    input: .../base_s.nc, ...
    output: .../base_s_10.nc, ...
    ...
INFO:__main__:The configured solver `highs` does not support quadratic objectives. Falling back to `scip`.
INFO:linopy.model: Solve problem using Scip solver
ERROR:root:Uncaught exception
Traceback...
ValueError: Solver scip does not support quadratic problems.
```

## Recommended Fix

To resolve this, we need to avoid the quadratic formulation in the clustering step or use a solver that supports it.

### Option A: Install a QP-capable solver
Install `ipopt` or `gurobi` (if licensed).

### Option B: Modify Configuration
The clustering distribution might be using a metric that requires QP. We can try to force a simple k-means or uniform distribution that doesn't trigger this optimization, or ensure the solver used can handle it.

However, since `highs` is usually sufficient for PyPSA-Eur, this might be a specific issue with how `distribute_n_clusters_to_countries` is implemented in this version.
