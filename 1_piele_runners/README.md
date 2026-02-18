# 🚀 Runners - Scenario Execution Scripts

Command runners for PyPSA-Eur simulations. These scripts execute energy system scenarios and generate network solutions.

## Python Runners

### **run_all_scenarios.py**
Executes all seasonal Romania scenarios.

**Scenarios Run:**
```
config/romania_2020_winter.yaml    → results/romania-2020-winter/
config/romania_2020_spring.yaml    → results/romania-2020-spring/
config/romania_2020_summer.yaml    → results/romania-2020-summer/
config/romania_2020_autumn.yaml    → results/romania-2020-autumn/
config/romania_2020_december.yaml  → results/romania-2020-december/
```

**How to Run:**
```bash
conda activate pypsa-eur
python run_all_scenarios.py
```

**Output:** Network files (*.nc) and CSV exports in results/

---

### **run_remaining_scenarios.py**
Executes a specific subset of seasonal scenarios (winter, spring, summer).

**Scenarios Run:**
```
config/romania_2020_winter.yaml    → results/romania-2020-winter/
config/romania_2020_spring.yaml    → results/romania-2020-spring/
config/romania_2020_summer.yaml    → results/romania-2020-summer/
```

**How to Run:**
```bash
conda activate pypsa-eur
python run_remaining_scenarios.py
```

**Use Case:** Run specific subset without waiting for all 5 scenarios

---

### **run_romania_winter_stress.py**
Executes baseline + stress winter 2019 scenarios and generates comparison report.

**Scenarios Run:**
```
Baseline:  config/adversarial/romania_2019_winter_baseline.yaml
Stress:    config/adversarial/romania_2019_winter_stress.yaml
Report:    Generates CSV comparison outputs
```

**Output:**
```
results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc
results/romania-2020-winter-stress/networks/base_s_10_elec_.nc
results/romania-2020-winter-stress-comparison/  (7 CSV files)
```

**How to Run:**
```bash
conda activate pypsa-eur
python run_romania_winter_stress.py
```

**Status:** ✅ WORKING - Generates winter stress comparison outputs

---

### **run_romania_winter_stress_direct.py**
Direct execution version of winter stress runner (alternative implementation).

**Scenarios Run:** Same as `run_romania_winter_stress.py`

**How to Run:**
```bash
conda activate pypsa-eur
python run_romania_winter_stress_direct.py
```

**Use Case:** Alternative if main version has issues; includes direct subprocess handling

---

## Batch/PowerShell Runners

### **run_scenario.bat** 
Windows batch script executing baseline + stress scenarios.

**Features:**
- Conda environment activation for Windows batch
- Snakemake workflow unlock before execution
- Multiple scenario solves with resource constraints

**How to Run:**
```cmd
cd c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur
run_scenario.bat
```

**Resources:** `mem_mb=32000` (32 GB RAM), `runtime=360` minutes

---

### **run_scenario_v2.bat**
Enhanced batch runner with improved error handling.

**Improvements:**
- Better error checking between steps
- Cleaner output structure
- More descriptive logging

**How to Run:**
```cmd
cd c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur
run_scenario_v2.bat
```

---

### **run_baseline_only.bat**
Simplified batch runner for baseline scenario only (no stress).

**Scenarios Run:**
```
config/adversarial/romania_2019_winter_baseline.yaml
```

**Output:**
```
results/romania-2020-winter-baseline/networks/
```

**How to Run:**
```cmd
cd c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur
run_baseline_only.bat
```

**Use Case:** Quick test without full stress scenario overhead

---

## Quick Reference

| Script | Scenarios | Duration | Status |
|--------|-----------|----------|--------|
| `run_all_scenarios.py` | All 5 seasonal | ~5-6 hours | ✅ WORKING |
| `run_remaining_scenarios.py` | 3 seasonal | ~3 hours | ✅ WORKING |
| `run_romania_winter_stress.py` | Baseline + Stress | ~2 hours | ✅ WORKING |
| `run_romania_winter_stress_direct.py` | Baseline + Stress | ~2 hours | ✅ WORKING |
| `run_scenario.bat` | Baseline + Stress | ~2 hours | ✅ WORKING |
| `run_scenario_v2.bat` | Baseline + Stress | ~2 hours | ✅ WORKING |
| `run_baseline_only.bat` | Baseline only | ~1 hour | ✅ WORKING |

---

## Resource Requirements

**Minimum:**
- RAM: 16 GB (will be slow)
- Disk: 20 GB for results
- Time: 1-2 hours per scenario

**Recommended:**
- RAM: 32 GB
- Disk: 50+ GB for full results
- CPU: 8+ cores
- Time: 30 minutes per scenario with resources

---

## Configuration Files

All runners use config files from `config/`:
```
config/
├── romania_2020_winter.yaml        (Winter scenario)
├── romania_2020_spring.yaml        (Spring scenario)
├── romania_2020_summer.yaml        (Summer scenario)
├── romania_2020_autumn.yaml        (Autumn scenario)
├── romania_2020_december.yaml      (December scenario)
└── adversarial/
    ├── romania_2019_winter_baseline.yaml
    └── romania_2019_winter_stress.yaml
```

Edit these configs to modify scenario parameters like:
- Temporal resolution (hourly snapshots)
- Spatial resolution (clustering)
- Technology constraints
- Solver parameters

---

## Troubleshooting

**"Solver scip does not support quadratic problems"**
- Try different solver (gurobi, cbc)
- Modify clustering algorithm in config

**"Out of memory"**
- Reduce spatial resolution (increase clustering)
- Close other applications
- Use `run_baseline_only.bat` for smaller run

**"Snakemake lock"**
- Run `snakemake --unlock` before executing
- Delete `.snakemake/locks/` folder if persistent

---

## Next Steps

After running scenarios:
1. View results with dashboard: `../dashboard/visualize_scenarios_ui_v2.py`
2. Analyze outputs in `results/` folder
3. Generate reports: See `../analysis/` folder
4. Check diagnostics: See `../diagnostics/` folder
