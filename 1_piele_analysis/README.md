# 📈 Analysis - Results Processing & Reporting

Post-processing scripts for analyzing and interpreting PyPSA-Eur simulation results. Includes configuration generation, data interpretation, and scenario comparison tools.

## Configuration Generation

### **generate_configs.py**
Generates Romania scenario configuration files.

**Purpose:** Create YAML configuration files with specified scenario parameters

**Generates:**
- Base Romania config template
- Scenario-specific settings
- Parameter tuning configurations

**How to Run:**
```bash
python generate_configs.py
```

**Output:** YAML files in `config/` directory

---

### **generate_adversarial_configs.py**
Generates 10 adversarial stress-test scenario configurations.

**Adversarial Scenarios Generated:**
1. **Nuclear Blackout** - Nuclear generation offline
2. **Hydro Drought** - Reduced hydro availability
3. **No Wind** - Wind resources unavailable
4. **Cloudy Winter** - Reduced solar output
5. **Gas Crisis** - Limited gas imports
6. **Peak Demand** - 20% higher electricity demand
7. **Grid Failure** - Transmission line outages
8. **Coal Phaseout** - Coal plants offline
9. **Import Isolation** - Interconnectors limited
10. **Combined Crisis** - Multiple failures
11. **Sibiu Regional Crisis** - Regional transmission failure

**Stress Test Philosophy:**
Test system resilience by simulating infrastructure failures, resource shocks, and demand spikes

**How to Run:**
```bash
python generate_adversarial_configs.py
```

**Output:** 
```
config/adversarial/
├── romania_adversarial_01_nuclear_blackout.yaml
├── romania_adversarial_02_hydro_drought.yaml
├── ... (10 scenarios total)
└── romania_adversarial_11_sibiu_regional_crisis.yaml
```

---

## Results Interpretation

### **interpret_results.py**
Interprets and summarizes solved network results.

**Input:** Network file (*.nc)

**Outputs:**
- System statistics (buses, generators, lines)
- Total system cost
- Generation capacities by carrier
- Annual generation mix
- Average marginal prices

**How to Run:**
```bash
python interpret_results.py
```

**Example Output:**
```
Network Statistics
  Buses: 10
  Lines: 8
  Generators: 19
  Loads: 10

Total Cost: 12.94 million EUR/a

Installed Capacities (GW):
  CCGT: 1.26
  Solar: 7.47
  Onwind: 5.51
  
Annual Generation (TWh):
  Solar: 0.0085
  Onwind: 0.0069
  Lignite: 0.0196
```

---

### **explore_scenarios.py**
Explores available scenarios and their characteristics.

**Purpose:** 
- Discover all scenarios in `results/` folder
- Display scenario metadata
- Compare scenario structures
- List available outputs

**How to Run:**
```bash
python explore_scenarios.py
```

**Output:**
```
Found 5 scenarios:
  1. romania-2020-winter-stress-comparison (NEW format, 7 CSVs)
  2. romania-2020-summer (LEGACY format, 14 CSVs)
  3. romania-2020-autumn (LEGACY format, 14 CSVs)
  4. romania-2020-spring (LEGACY format, 14 CSVs)
  5. romania-2020-december (LEGACY format, 14 CSVs)
```

---

### **summarize_results.py**
Generates summary tables of simulation results.

**Input:** Network file (*.nc)

**Outputs:**
- Markdown tables with key metrics
- Installed capacities by carrier
- Annual generation by technology
- Marginal price statistics

**How to Run:**
```bash
python summarize_results.py
```

**Example Output:**
```markdown
# PyPSA-Eur Simulation Results

## Installed Capacities [GW]
| Carrier  | Capacity |
|----------|----------|
| CCGT     | 1.26     |
| Solar    | 7.47     |
| Onwind   | 5.51     |

## Annual Generation [TWh]
| Carrier  | Energy  |
|----------|---------|
| Solar    | 0.0085  |
| Onwind   | 0.0069  |
```

---

### **run_summary.py**
Orchestrates summary generation for multiple scenarios.

**Purpose:**
- Batch process summary generation
- Create reports for seasonal scenarios
- Generate comparison plots

**Scenarios Processed:**
```
romania-2020-december
romania-2020-autumn
romania-2020-spring
romania-2020-summer
```

**How to Run:**
```bash
python run_summary.py
```

**Outputs:**
- Summary CSV files
- Comparison plots (PNG/PDF)
- Summary markdown tables

---

## Failure Analysis

### **analyze_scenario_11.py**
Analyzes Scenario 11 (Sibiu Regional Crisis) simulation failures.

**Documentation:** [scenario_11_failure_log.md](../docs/scenario_11_failure_log.md)

**Failure Analysis:**
- Clustering algorithm quadratic optimization issues
- Solver compatibility problems (scip vs gurobi)
- Network resilience under regional failure

**How to Run:**
```bash
python analyze_scenario_11.py
```

**Purpose:** 
Understand why certain adversarial scenarios fail and what constraints need adjustment

---

## Analysis Workflow

**Typical Workflow:**
```
1. Generate configurations
   python generate_adversarial_configs.py

2. Run scenarios (see ../runners/)
   python ../runners/run_all_scenarios.py

3. Interpret results
   python interpret_results.py

4. Summarize findings
   python run_summary.py

5. Explore scenarios
   python explore_scenarios.py

6. Visualize (see ../dashboard/)
   python ../dashboard/visualize_scenarios_ui_v2.py
```

---

## File Organization

```
analysis/
├── generate_configs.py              # Create scenario configs
├── generate_adversarial_configs.py  # Create stress tests
├── interpret_results.py             # Read network results
├── explore_scenarios.py             # Discover scenarios
├── summarize_results.py             # Create summary tables
├── run_summary.py                   # Batch summaries
└── analyze_scenario_11.py           # Failure analysis
```

---

## Data Input/Output

**Inputs:**
```
results/
├── romania-2020-winter-baseline/networks/*.nc
├── romania-2020-winter-stress/networks/*.nc
└── romania-2020-*/csvs/*.csv
```

**Outputs:**
```
results/
├── romania-2020-*/                  # Summary CSVs
└── romania-2020-*-comparison/       # Comparison reports
```

---

## Common Analysis Tasks

### Task 1: Compare baseline vs. stress
```bash
python interpret_results.py  # Run after both scenarios
```

### Task 2: Generate all scenario summaries
```bash
python run_summary.py
```

### Task 3: Explore available data
```bash
python explore_scenarios.py
```

### Task 4: Analyze adversarial scenario
```bash
python analyze_scenario_11.py
```

### Task 5: Generate config for new scenario
```bash
python generate_adversarial_configs.py
```

---

## Documentation

- [PLAN.md](../docs/PLAN.md) - Original project plan
- [scenario_11_failure_log.md](../docs/scenario_11_failure_log.md) - Scenario 11 analysis
- [results_summary.md](../docs/results_summary.md) - Example output

---

## Next Steps

1. **After running scenarios:** Use `summarize_results.py` to generate tables
2. **For visualization:** See `../dashboard/visualize_scenarios_ui_v2.py`
3. **For detailed diagnostics:** See `../diagnostics/`
4. **For data download:** See `../data_download/`
