# PlanUI Implementation Notes

## Overview
`PlanUI` is a Tkinter desktop program that adds:
- Scenario Wizard with two editing modes:
- Core + Stress controls
- Advanced YAML editor with read-only template panel
- Run manager with queue (`1 active + queued`), cancellation, logs, and spinner
- New-format results browser for report outputs like `results/romania-2020-winter-stress-comparison`
- Bilingual UI (`en` / `ro`)
- Persistent state for language, UI selections, and queue/history

Main entrypoint:
- `1_piele_dashboard/scenario_manager_ui.py`

Core package:
- `1_piele_dashboard/scenario_manager/`

Canonical template:
- `1_piele_docs/scenario_template.yaml`

## Run Modes
## 1. Paired
Creates baseline + scenario configs, runs both with Snakemake, then generates comparison report.

## 2. Single
Requires a reference baseline `.nc` network from existing results, runs only scenario solve, then generates comparison report using selected baseline.

## Naming and Validation
- `output_name` is required.
- `results/<output_name>` must not already exist.
- Generated configs are written to:
- `config/adversarial/generated/`
- Run names are slug-derived and timestamped.

## Required New-Format Result Files
The results page lists only folders containing all files:
- `system_cost_comparison.csv`
- `generation_mix_mwh.csv`
- `lmp_summary_ro.csv`
- `ens_summary.csv`
- `curtailment_mwh.csv`
- `daily_net_imports_mwh.csv`
- `interconnector_flow_congestion.csv`

## State Persistence
State file:
- `1_piele_dashboard/scenario_manager_state.json`

Persisted data:
- language
- queue/history jobs
- basic UI fields

Restart behavior:
- jobs previously marked `running` are re-labeled `interrupted`
- no attempt is made to reattach to old OS processes

## Command Assumptions
Commands run in the active environment:
- `snakemake ...`
- `python scripts/report_romania_winter_stress.py ...`

## Quick Usage
1. Launch:
```bash
python 1_piele_dashboard/scenario_manager_ui.py
```
2. In `Scenario Builder`, set controls or edit YAML.
3. In `Runs`, enqueue one or more jobs.
4. Watch queue/status while navigating pages.
5. In `Results`, pick a detected output and browse summary/CSV/figures/assumptions.

## Tests Added
File:
- `test/test_scenario_manager.py`

Covered:
- template immutability and paired config generation
- single mode baseline validation
- results indexing only for complete new-format folders
- restart behavior marking `running -> interrupted`
- queue processing (`running + queued`) and failed command handling

