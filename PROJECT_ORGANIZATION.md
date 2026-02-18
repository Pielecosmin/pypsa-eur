# PyPSA-Eur Romania - Project Organization Guide

Welcome to the PyPSA-Eur Romania Analysis project! This guide explains the new folder structure created January 2026, organizing all custom analysis tools and workflows.

## 📁 Folder Structure Overview

```
pypsa-eur/
│
├── 📊 1_piele_dashboard/            → Interactive visualization dashboards
│   ├── visualize_scenarios_ui.py    (v1 - baseline vs. stress)
│   ├── visualize_scenarios_ui_v2.py (v2 - dynamic scenarios)
│   ├── test_legacy_display.py       (data validation)
│   └── README.md                    (full guide)
│
├── 🚀 1_piele_runners/              → Scenario execution scripts
│   ├── run_all_scenarios.py         (execute all 5 seasons)
│   ├── run_remaining_scenarios.py   (execute 3 seasons)
│   ├── run_romania_winter_stress.py (baseline + stress)
│   ├── run_romania_winter_stress_direct.py
│   ├── *.bat files                  (Windows batch runners)
│   └── README.md                    (full guide)
│
├── 📈 1_piele_analysis/             → Results processing & reporting
│   ├── generate_configs.py          (create scenario configs)
│   ├── generate_adversarial_configs.py (create 10 stress tests)
│   ├── interpret_results.py         (analyze network results)
│   ├── explore_scenarios.py         (discover available scenarios)
│   ├── summarize_results.py         (generate summary tables)
│   ├── run_summary.py               (batch processing)
│   ├── analyze_scenario_11.py       (failure analysis)
│   └── README.md                    (full guide)
│
├── 🔍 1_piele_diagnostics/          → Testing & validation tools
│   ├── check_csv.py                 (validate CSV data)
│   ├── check_romania.py             (validate configs)
│   ├── check_url.py                 (test data sources)
│   ├── test_snakemake.ps1           (test workflow DAG)
│   └── README.md                    (full guide)
│
├── 📥 1_piele_data_download/        → External data acquisition
│   ├── download_cutout.py           (download weather data)
│   ├── download_zenodo_files.py     (download datasets)
│   └── README.md                    (full guide)
│
├── 📚 1_piele_docs/                 → Project documentation
│   ├── PLAN.md                      (original project plan)
│   ├── DASHBOARD_README.md          (v1 guide)
│   ├── VISUALIZER_COMPARISON.md     (v1 vs v2)
│   ├── DASHBOARD_V2_IMPLEMENTATION.md (v2 technical)
│   ├── FORMAT_SUPPORT.md            (data format specs)
│   ├── romania_config_explanation.md (config guide EN)
│   ├── romania_config_explanation_ro.md (config guide RO)
│   ├── results_summary.md           (example results)
│   ├── scenario_11_failure_log.md   (failure analysis)
│   ├── README2.md & README3.md      (supplementary)
│   └── README.md                    (docs index)
│
├── 🌍 Original PyPSA-Eur Folders
│   ├── config/                      (configuration files)
│   ├── scripts/                     (main workflow scripts)
│   ├── rules/                       (Snakemake rules)
│   ├── data/                        (input datasets)
│   ├── results/                     (scenario outputs)
│   ├── resources/                   (preprocessed data)
│   ├── benchmarks/                  (performance data)
│   ├── doc/                         (original documentation)
│   └── ... (other standard folders)
│
└── 📝 Root Level Files
    ├── README.md                     (main project readme)
    ├── Snakefile                     (workflow definition)
    ├── pixi.toml                     (dependency management)
    └── ... (other config files)
```

---

## 🚀 Quick Start Workflows

### Workflow 1: View Existing Results
**Time:** 2 minutes | **Skills:** None required

```bash
# Navigate to dashboard folder and run v2
cd 1_piele_dashboard
python visualize_scenarios_ui_v2.py

# Tips:
# 1. Select scenario from dropdown
# 2. Click tabs to explore data
# 3. Use "Browse" for custom folder selection
```

**See:** [1_piele_dashboard/README.md](1_piele_dashboard/README.md)

---

### Workflow 2: Run New Scenarios
**Time:** 1-6 hours | **Skills:** PyPSA, Snakemake basic knowledge

```bash
# 1. Validate environment
cd 1_piele_diagnostics
python check_romania.py

# 2. Run baseline scenario only (quick test)
cd ../1_piele_runners
run_baseline_only.bat

# 3. View results with dashboard
cd ../1_piele_dashboard
python visualize_scenarios_ui_v2.py
```

**See:** [1_piele_runners/README.md](1_piele_runners/README.md)

---

### Workflow 3: Analyze & Generate Reports
**Time:** 30 minutes | **Skills:** Python, data analysis

```bash
# 1. Generate scenario summaries
cd 1_piele_analysis
python run_summary.py

# 2. Explore available scenarios
python explore_scenarios.py

# 3. Interpret specific results
python interpret_results.py

# 4. Visualize outputs
cd ../1_piele_dashboard
python visualize_scenarios_ui_v2.py
```

**See:** [1_piele_analysis/README.md](1_piele_analysis/README.md)

---

### Workflow 4: Stress-Test Scenarios
**Time:** 2+ hours | **Skills:** Advanced - Network understanding

```bash
# 1. Generate adversarial configs
cd 1_piele_analysis
python generate_adversarial_configs.py

# 2. Run specific scenario via runners
cd ../1_piele_runners
python run_romania_winter_stress.py

# 3. Analyze failure cases
cd ../1_piele_analysis
python analyze_scenario_11.py
```

**See:** [1_piele_analysis/README.md](1_piele_analysis/README.md)

---

### Workflow 5: Troubleshoot Issues
**Time:** 15-45 minutes | **Skills:** Debugging

```bash
# 1. Check data sources
cd 1_piele_diagnostics
python check_url.py

# 2. Validate configurations
python check_romania.py

# 3. Check output data quality
python check_csv.py

# 4. Test Snakemake workflow
.\test_snakemake.ps1
```

**See:** [1_piele_diagnostics/README.md](1_piele_diagnostics/README.md)

---

## 📚 Finding What You Need

### I want to...

**View existing simulation results**
→ See [1_piele_dashboard/README.md](1_piele_dashboard/README.md)

**Run a new scenario**
→ See [1_piele_runners/README.md](1_piele_runners/README.md)

**Generate reports & analysis**
→ See [1_piele_analysis/README.md](1_piele_analysis/README.md)

**Validate data or configuration**
→ See [1_piele_diagnostics/README.md](1_piele_diagnostics/README.md)

**Download missing datasets**
→ See [1_piele_data_download/README.md](1_piele_data_download/README.md)

**Understand the project**
→ See [1_piele_docs/README.md](1_piele_docs/README.md)

**Configure a scenario**
→ See [1_piele_docs/romania_config_explanation.md](1_piele_docs/romania_config_explanation.md)

**Understand data formats**
→ See [1_piele_docs/FORMAT_SUPPORT.md](1_piele_docs/FORMAT_SUPPORT.md)

---

## 🔄 Typical User Journeys

### Journey 1: Quick Visualization
```
User: "I just want to see the results"

Steps:
1. cd 1_piele_dashboard
2. python visualize_scenarios_ui_v2.py
3. Select scenario → Explore tabs

Time: 2 minutes
Skills: None
Result: Interactive dashboard open
```

---

### Journey 2: Run & Analyze
```
User: "I want to run a scenario and see results"

Steps:
1. cd 1_piele_runners
2. run_baseline_only.bat (quick test)
3. cd ../1_piele_analysis
4. python run_summary.py
5. cd ../1_piele_dashboard
6. python visualize_scenarios_ui_v2.py

Time: 1-2 hours
Skills: Basic
Result: New scenario results visualized
```

---

### Journey 3: Full Workflow
```
User: "I want to do everything"

Steps:
1. cd 1_piele_diagnostics
   python check_romania.py    (validate)
2. cd ../1_piele_runners
   run_all_scenarios.py       (run all 5)
3. cd ../1_piele_analysis
   python run_summary.py      (analyze)
4. cd ../1_piele_dashboard
   python visualize_scenarios_ui_v2.py (view)

Time: 6-8 hours
Skills: Intermediate
Result: Complete analysis suite
```

---

### Journey 4: Troubleshoot
```
User: "Something failed, help!"

Steps:
1. cd 1_piele_diagnostics
   python check_url.py        (data sources?)
   python check_romania.py    (config?)
   python check_csv.py        (data integrity?)
   .\test_snakemake.ps1       (workflow?)
2. Check error logs in logs/
3. Consult 1_piele_docs/scenario_11_failure_log.md

Time: 15-45 minutes
Skills: Debugging
Result: Issue identified & resolved
```

---

## 📖 Documentation Map

| Document | Purpose | Link |
|----------|---------|------|
| **Getting Started** | New users intro | [1_piele_docs/PLAN.md](1_piele_docs/PLAN.md) |
| **Dashboard Guide** | UI walkthrough | [1_piele_docs/DASHBOARD_README.md](1_piele_docs/DASHBOARD_README.md) |
| **Data Formats** | Understand data structure | [1_piele_docs/FORMAT_SUPPORT.md](1_piele_docs/FORMAT_SUPPORT.md) |
| **Config Guide** | Modify scenarios | [1_piele_docs/romania_config_explanation.md](1_piele_docs/romania_config_explanation.md) |
| **v2 Technical** | Implementation details | [1_piele_docs/DASHBOARD_V2_IMPLEMENTATION.md](1_piele_docs/DASHBOARD_V2_IMPLEMENTATION.md) |
| **Failures** | Known issues | [1_piele_docs/scenario_11_failure_log.md](1_piele_docs/scenario_11_failure_log.md) |

---

## ⚡ Key Features by Folder

| Folder | Features | Status |
|--------|----------|--------|
| **1_piele_dashboard/** | v1+v2 visualization, 6 taburi, live data | ✅ Production |
| **1_piele_runners/** | 7 execution scripts, batch+Python | ✅ Tested |
| **1_piele_analysis/** | Config generation, summaries, reporting | ✅ Ready |
| **1_piele_diagnostics/** | Validation, testing, troubleshooting | ✅ Ready |
| **1_piele_data_download/** | ERA5 weather, Zenodo datasets | ✅ Ready |
| **1_piele_docs/** | Comprehensive guides (EN/RO) | ✅ Complete |

---

## 🎯 Organization Benefits

**Before (Root Directory - Cluttered):**
```
pypsa-eur/
├── visualize_scenarios_ui.py     (What is this?)
├── visualize_scenarios_ui_v2.py  (Different version?)
├── download_cutout.py            (Data related?)
├── run_all_scenarios.py          (Runner?)
├── generate_adversarial_configs.py
├── check_csv.py                  (Validation?)
├── analyze_scenario_11.py        (Analysis?)
└── 20+ more files...
```
**Problem:** No clear purpose, hard to navigate

---

**After (Organized Structure):**
```
pypsa-eur/
├── 📊 1_piele_dashboard/        → All visualization (3 files)
├── 🚀 1_piele_runners/          → All runners (7 files)
├── 📈 1_piele_analysis/         → All analysis (6 files)
├── 🔍 1_piele_diagnostics/      → All validation (4 files)
├── 📥 1_piele_data_download/    → All downloads (2 files)
└── 📚 1_piele_docs/             → All documentation (12+ files)
```
**Benefit:** Clear purpose, easy to find, logical workflow at top

---

## 🔗 Integration Points

```
workflow: data → run → analyze → visualize → understand

1. Data Download (1_piele_data_download/)
   └─→ Check with 1_piele_diagnostics/check_url.py
   
2. Configuration (config/)
   └─→ Validate with 1_piele_diagnostics/check_romania.py
   
3. Scenario Execution (1_piele_runners/)
   └─→ Check with 1_piele_diagnostics/check_csv.py
   
4. Analysis (1_piele_analysis/)
   └─→ Generate summaries
   
5. Visualization (1_piele_dashboard/)
   └─→ v2 auto-detects format & renders
   
6. Understanding (1_piele_docs/)
   └─→ Reference throughout
```

---

## 📋 Folder Checklist

After organizing, verify:

- [x] **1_piele_dashboard/** - Contains 3 .py files + README
- [x] **1_piele_runners/** - Contains 7 script files + README
- [x] **1_piele_analysis/** - Contains 6 .py files + README
- [x] **1_piele_diagnostics/** - Contains 4 validation files + README
- [x] **1_piele_data_download/** - Contains 2 .py files + README
- [x] **1_piele_docs/** - Contains 12+ .md files + README
- [x] All READMEs created with clear purposes
- [x] Cross-references between folders working
- [x] Original PyPSA-Eur structure preserved

---

## 🎓 Learning Path

**Beginner (Want to view results):**
1. Read: [1_piele_dashboard/README.md](1_piele_dashboard/README.md)
2. Run: `python 1_piele_dashboard/visualize_scenarios_ui_v2.py`
3. Explore: Click through tabs

**Intermediate (Want to run scenarios):**
1. Read: [1_piele_runners/README.md](1_piele_runners/README.md)
2. Run: `python 1_piele_runners/run_baseline_only.bat`
3. Analyze: See [1_piele_analysis/README.md](1_piele_analysis/README.md)
4. Visualize: Use dashboard

**Advanced (Want to modify everything):**
1. Read: [1_piele_docs/README.md](1_piele_docs/README.md)
2. Understand: [1_piele_docs/PLAN.md](1_piele_docs/PLAN.md)
3. Configure: Edit `config/*.yaml`
4. Generate: Use [1_piele_analysis/generate_adversarial_configs.py](1_piele_analysis/generate_adversarial_configs.py)
5. Run: Use [1_piele_runners/](1_piele_runners/)
6. Analyze: Use [1_piele_analysis/](1_piele_analysis/)

---

## 📝 Last Updated

**Date:** January 2026  
**Changes:** Project reorganization after 7 January 2026  
**Files Organized:** 30+ custom analysis files into 6 logical folders  
**Documentation:** 12+ files with cross-references

---

## 🆘 Need Help?

1. **Can't find a file?** → Check [1_piele_docs/README.md](1_piele_docs/README.md) (file index)
2. **How to use dashboard?** → See [1_piele_dashboard/README.md](1_piele_dashboard/README.md)
3. **How to run scenarios?** → See [1_piele_runners/README.md](1_piele_runners/README.md)
4. **Data validation?** → See [1_piele_diagnostics/README.md](1_piele_diagnostics/README.md)
5. **Results analysis?** → See [1_piele_analysis/README.md](1_piele_analysis/README.md)
6. **Understand project?** → See [1_piele_docs/PLAN.md](1_piele_docs/PLAN.md)

---

## 🌟 Quick Links

- **Main Dashboard:** `python 1_piele_dashboard/visualize_scenarios_ui_v2.py`
- **Run All Scenarios:** `python 1_piele_runners/run_all_scenarios.py`
- **Quick Test:** `python 1_piele_runners/run_baseline_only.bat`
- **Analyze Results:** `python 1_piele_analysis/explorer_scenarios.py`
- **Generate Reports:** `python 1_piele_analysis/run_summary.py`
- **Validate Data:** `python 1_piele_diagnostics/check_csv.py`

---

**Happy analyzing! 🚀**
