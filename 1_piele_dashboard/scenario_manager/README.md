# Scenario Manager

`scenario_manager` provides the backend modules used by `1_piele_dashboard/scenario_manager_ui.py`.

## What It Does
- Builds scenario configs from a read-only template.
- Creates command sequences for Snakemake + reporting.
- Runs jobs through a single active worker with queue support.
- Persists queue/history and UI state to disk.
- Indexes and parses new-format result folders.
- Supports static bilingual labels (EN/RO).

## Module Map
- `types.py`: dataclasses and core typed structures.
- `config_builder.py`: config generation, naming, command assembly.
- `run_manager.py`: queue, subprocess execution, cancel/status transitions.
- `results_index.py`: detect required CSV outputs and parse summaries.
- `state_store.py`: load/save JSON state and restart handling.
- `i18n.py`: translation keys and helper function.

## Related Files
- UI entrypoint: `1_piele_dashboard/scenario_manager_ui.py`
- Canonical template: `1_piele_docs/scenario_template.yaml`
- Implementation notes: `1_piele_docs/planui.md`
- Tests: `test/test_scenario_manager.py`

## Run
From repository root:

```bash
python 1_piele_dashboard/scenario_manager_ui.py
```

The app assumes the active environment already has `snakemake`, `python`, and required project dependencies.
If `snakemake` is missing in the current interpreter, the app automatically falls back to:
- `conda run -n <selected_env> python -m snakemake ...`
- `conda run -n <selected_env> python scripts/report_romania_winter_stress.py ...`

Conda env selection order:
- `PLANUI_CONDA_PREFIX` (if set and path exists)
- default prefix `C:\Users\Administrator\.conda\envs\pypsa-eur` (if path exists)
- `PLANUI_CONDA_ENV` (if set)
- active conda env (`CONDA_DEFAULT_ENV`) when not `base`
- `pypsa`
- `pypsa-eur`

You can force a specific env path or env name with:
- `PLANUI_CONDA_PREFIX`
- `PLANUI_CONDA_ENV`

## State and Logs
- State file: `1_piele_dashboard/scenario_manager_state.json`
- Job logs: `logs/planui/*.log`

## Result Format
The results page includes only folders containing all required report CSVs:
- `system_cost_comparison.csv`
- `generation_mix_mwh.csv`
- `lmp_summary_ro.csv`
- `ens_summary.csv`
- `curtailment_mwh.csv`
- `daily_net_imports_mwh.csv`
- `interconnector_flow_congestion.csv`
