# PlanUI: Scenario Wizard + Run Manager + New-Format Results Viewer

## Summary
Build a new Tkinter desktop application that lets you create scenarios via guided controls or advanced YAML editing, enqueue and run Snakemake workflows without blocking navigation, and view only the new report-format outputs (like `results/romania-2020-winter-stress-comparison`) from a self-updating results list.  
The implementation will also add a read-only canonical template in docs and produce implementation documentation at `1_piele_docs/planui.md`.

## Scope
- In scope: new Python app, config generation, queue-based run execution, spinner/status UI, always-available page navigation, self-updating new-format results page, bilingual toggle (EN/RO), persistent run/history state.
- Out of scope: auto-reattach to already-running OS processes after app restart, legacy-format results rendering, overwrite behavior for existing output names.

## Target Files
- `1_piele_docs/planui.md`
- `1_piele_docs/scenario_template.yaml`
- `1_piele_dashboard/scenario_manager_ui.py`
- `1_piele_dashboard/scenario_manager/types.py`
- `1_piele_dashboard/scenario_manager/config_builder.py`
- `1_piele_dashboard/scenario_manager/run_manager.py`
- `1_piele_dashboard/scenario_manager/results_index.py`
- `1_piele_dashboard/scenario_manager/state_store.py`
- `1_piele_dashboard/scenario_manager/i18n.py`

## App Architecture
1. Navigation shell:
- Sidebar/top nav with pages always accessible: `Scenario Builder`, `Runs`, `Results`.
- Global language toggle EN/RO.
- Global active-run spinner indicator.

2. Scenario Builder page:
- Run mode selector: `Paired (baseline+scenario)` or `Single scenario with reference baseline`.
- Two editing modes:
- `Core + Stress Controls`: structured form fields update an in-memory working config.
- `Advanced YAML`: editable working YAML panel plus read-only canonical template panel.
- Template source is fixed: `1_piele_docs/scenario_template.yaml`.
- Template file is never modified.

3. Runs page:
- Job submission form and queue list.
- Status lifecycle: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `interrupted`.
- One active job max; additional jobs queued.
- Per-job logs path and progress text.
- Spinner visible while any job is `running`.

4. Results page:
- Auto-refresh index (polling) of new-format result folders only.
- Selection list from `results/` updates while app runs.
- Native tabs for selected result:
- `Summary` (cost delta, ENS, imports, price stats).
- `CSV Data` (dropdown/table preview for required CSVs).
- `Figures` (PNG picker and image viewer).
- `Assumptions` (markdown/text panel).

## Run Flows
1. Paired flow:
- Generate `baseline` config by cloning scenario config and forcing `stress_test.enable=false`.
- Generate `scenario` config with stress settings.
- Execute commands in active environment:
- `snakemake --unlock --configfile <baseline_cfg>`
- `snakemake -c all <baseline_target_nc> --configfile <baseline_cfg>`
- `snakemake --unlock --configfile <scenario_cfg>`
- `snakemake -c all <scenario_target_nc> --configfile <scenario_cfg>`
- `python scripts/report_romania_winter_stress.py --baseline-net <baseline_target_nc> --scenario-net <scenario_target_nc> --country <country> --outdir results/<output_name>`

2. Single flow:
- Require user-selected solved baseline network from discovered list (`results/*/networks/*.nc`).
- Run only scenario config solve, then report using selected baseline network:
- `snakemake --unlock --configfile <scenario_cfg>`
- `snakemake -c all <scenario_target_nc> --configfile <scenario_cfg>`
- `python scripts/report_romania_winter_stress.py --baseline-net <selected_baseline_nc> --scenario-net <scenario_target_nc> --country <country> --outdir results/<output_name>`

## Naming and Validation Rules
- User-provided output name is required.
- If `results/<output_name>` exists, submission is blocked and rename is required.
- Generated config files go to `config/adversarial/generated/`.
- Run names derived from user scenario slug to keep uniqueness and traceability.
- Required new-format CSVs for result eligibility:
- `system_cost_comparison.csv`
- `generation_mix_mwh.csv`
- `lmp_summary_ro.csv`
- `ens_summary.csv`
- `curtailment_mwh.csv`
- `daily_net_imports_mwh.csv`
- `interconnector_flow_congestion.csv`

## Persistent State
- Persist queue/history/settings in JSON at app-level state file.
- On restart:
- Reload completed/failed history.
- Mark previously `running` jobs as `interrupted` (no auto-reattach).
- Keep language and last UI selections.

## Public Interfaces and Types
- `ScenarioInputs`: run mode, names, country, snapshots, clusters, solver, stress params, reference baseline path.
- `ConfigBuildResult`: generated config file paths, run names, expected network targets.
- `JobSpec`: command list, output_name, mode, created_at.
- `JobRecord`: job_id, status, timestamps, output_dir, log_path, exit_code, error_summary.
- `ResultEntry`: folder path, detected files, timestamp, validity flags.
- `scan_new_format_results(results_dir) -> list[ResultEntry]`
- `build_configs(inputs, template_path) -> ConfigBuildResult`
- `enqueue(job_spec)`, `cancel(job_id)`, `load_state()`, `save_state()`.

## Test Cases and Scenarios
1. Config/template:
- Template hash unchanged after both editing modes.
- Paired build creates two YAMLs and baseline has `stress_test.enable=false`.
- Single build requires valid baseline network path.

2. Queue/runtime:
- Submitting two jobs yields one `running`, one `queued`.
- Navigation remains responsive during long running subprocess.
- Failed command marks job `failed` with captured stderr snippet.
- Restart reloads history and converts stale `running` to `interrupted`.

3. Results indexing/viewing:
- Only folders with all 7 required CSVs appear.
- New result folder appears without restart during polling.
- Summary metrics parse correctly from sample comparison output.
- Figures/assumptions tabs handle missing optional files gracefully.

4. UX rules:
- Bilingual toggle updates visible labels on all pages.
- Name conflict blocks submission.
- Spinner appears only when any job is active.

## Implementation Sequence
1. Create `1_piele_docs/scenario_template.yaml` and `1_piele_docs/planui.md`.
2. Implement shared types, i18n map, and state store.
3. Implement config builder with immutable-template workflow.
4. Implement run manager queue and subprocess orchestration.
5. Implement results indexer and parser for required new-format files.
6. Build Tkinter shell + 3 pages + always-available navigation.
7. Add persistence/reload behavior and polling loops.
8. Add tests and a short usage section in `1_piele_docs/planui.md`.

## Assumptions and Defaults
- App runs in already-activated environment and uses plain `snakemake`/`python`.
- Poll intervals default to 5 seconds for queue and results refresh.
- Results page is new-format only.
- No overwrite behavior is allowed for existing output folders.
- Bilingual support uses static key-based translations (EN/RO), no external i18n dependency.
