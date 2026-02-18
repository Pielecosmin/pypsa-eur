# 🔍 Diagnostics - Testing & Validation Tools

Diagnostic scripts for validating configurations, checking data integrity, and testing infrastructure.

## Data Validation Scripts

### **check_csv.py**
Validates CSV data structures and format consistency.

**Purpose:**
- Verify CSV files are not corrupted
- Check column names and data types
- Detect missing values
- Validate data ranges

**How to Run:**
```bash
python check_csv.py
```

**Checks:**
- File integrity
- Column consistency
- Data type validation
- Missing value detection

---

### **check_romania.py**
Romania-specific configuration and data validation.

**Purpose:**
- Validate Romania scenario configs
- Check geographic data consistency
- Verify network topology
- Validate boundary conditions

**How to Run:**
```bash
python check_romania.py
```

**Validates:**
- Config file syntax (YAML)
- Geographic scope (Romania + neighboring countries)
- Network connectivity
- Bus/line/generator counts

---

### **check_url.py**
Tests connectivity and validates data download URLs.

**Purpose:**
- Check if data sources are accessible
- Validate download URLs
- Test network connectivity
- Verify file availability

**How to Run:**
```bash
python check_url.py
```

**Checks:**
- URL accessibility
- Download success
- File integrity post-download
- Retry logic for transient failures

---

## Workflow Testing

### **test_snakemake.ps1**
PowerShell script for testing Snakemake workflow.

**Purpose:**
- Validate Snakemake configuration
- Test workflow DAG (Directed Acyclic Graph)
- Dry-run simulations
- Check rule dependencies

**How to Run (PowerShell):**
```powershell
cd c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur
.\test_snakemake.ps1
```

**Operations:**
```powershell
# Initialize conda
conda init PowerShell

# Activate environment
conda activate pypsa-eur

# Dry-run with baseline config
snakemake -n --configfile config/adversarial/romania_2019_winter_baseline.yaml

# Check rule graph
snakemake --rulegraph | dot -Tpng -o workflow.png
```

**Outputs:**
- Dry-run execution plan
- DAG visualization (PNG)
- Rule dependency graph
- Estimated execution time

---

## Diagnostic Workflow

**Pre-Execution Checklist:**
```
1. Validate data source URLs
   python check_url.py

2. Validate configurations
   python check_romania.py

3. Check existing output CSVs
   python check_csv.py

4. Test Snakemake DAG
   .\test_snakemake.ps1

5. Run minimal scenario
   ..\runners\run_baseline_only.bat

6. Validate results
   python check_csv.py (on results/)
```

---

## Common Diagnostic Tasks

### Task 1: Verify data downloads
```bash
python check_url.py
```
**Output:** Confirms all data sources are accessible

### Task 2: Validate scenario config
```bash
python check_romania.py
```
**Output:** Confirms Romania scenario is properly configured

### Task 3: Check output data quality
```bash
python check_csv.py
# Point to: results/romania-2020-*/csvs/
```
**Output:** No errors = CSVs are valid

### Task 4: Preview Snakemake execution
```powershell
.\test_snakemake.ps1
```
**Output:** Shows what will be executed without running it

### Task 5: Diagnose simulation failure
```
1. Run test_snakemake.ps1 to check DAG
2. Run check_csv.py on input data
3. Analyze error logs in logs/ directory
4. Check resource constraints (RAM, disk)
```

---

## Troubleshooting Guide

| Problem | Diagnostic | Solution |
|---------|-----------|----------|
| Download fails | `check_url.py` | Check internet/proxy, retry |
| Config error | `check_romania.py` | Fix YAML syntax in config/ |
| CSV corrupted | `check_csv.py` | Re-download or regenerate |
| Snakemake hangs | `test_snakemake.ps1` | Check DAG for cycles, unlock |
| Out of memory | CPU monitoring + `test_snakemake.ps1` | Reduce spatial resolution |
| Solver issues | Check gurobi.log | Try different solver/algorithm |

---

## File Organization

```
diagnostics/
├── check_csv.py              # CSV validation
├── check_romania.py          # Config validation
├── check_url.py              # URL/download validation
└── test_snakemake.ps1        # Workflow testing (PowerShell)
```

---

## Integration with Other Tools

**Before Running Scenarios:**
```
diagnostics/ → validation → runners/ → dashboard/
   check_url.py
   check_romania.py
                    ↓
            run_baseline_only.bat
                    ↓
            visualize_scenarios_ui_v2.py
```

**After Running Scenarios:**
```
runners/ → diagnostics → analysis/ → dashboard/
           check_csv.py
           test_snakemake.ps1
                    ↓
            run_summary.py
                    ↓
            visualize_scenarios_ui_v2.py
```

---

## Log Files

When diagnostics fail, check:
```
logs/
├── romania-2020-*/solve_network/    # Snakemake logs
├── gurobi.log                       # Solver logs
└── run.log                          # Workflow logs
```

---

## Next Steps

1. **For data download issues:** Run `check_url.py` first
2. **For configuration issues:** Run `check_romania.py`
3. **For output validation:** Run `check_csv.py` on results
4. **For workflow issues:** Run `test_snakemake.ps1`
5. **To run scenarios:** See `../runners/`
6. **To view results:** See `../dashboard/`
