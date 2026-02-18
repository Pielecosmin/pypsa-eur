## Romania Winter 2019 Stress Scenario (Baseline + Shocked) in PyPSA-Eur

### Summary
Implement two new reproducible runs and one comparison report:
1. `Baseline` run with no shocks.
2. `Stress` run with all requested Romania shocks in one solve.
3. Automated post-processing that emits required CSVs, PNG/PDF figures, and a 1-page assumptions/limitations note.

This plan uses:
- Geographic scope: `RO + BG + HU + RS` (shocks applied only to Romania).
- Time window in snapshots (UTC): **2019-01-13 22:00 to 2019-01-20 22:00**, `inclusive: left`, hourly (168 snapshots).  
  This matches local EET: **2019-01-14 00:00 to 2019-01-21 00:00**.
- Hybrid ops mode: no generation/storage/H2 expansion, but limited transmission expansion (`+500 MW` per line/link).
- SCADA proxy: ramp cap `10%/h` for first 24h, then `25%/h` for next 48h.

### Files To Add
1. `config/adversarial/romania_2019_winter_baseline.yaml`
2. `config/adversarial/romania_2019_winter_stress.yaml`
3. `scripts/romania_winter_stress.py`
4. `scripts/report_romania_winter_stress.py`
5. `run_romania_winter_stress.py`
6. `test/test_romania_winter_stress.py`

### Files To Modify
1. `scripts/solve_network.py`  
   Add pre-model shock application call and post-model custom constraints call.

---

### 1) Config Implementation

Create `baseline` and `stress` configs with:
1. `run.name` as:
   - `romania-2019-winter-baseline`
   - `romania-2019-winter-stress`
2. `countries: [RO, BG, HU, RS]`
3. `scenario.clusters: [10]`, `scenario.opts: ['']`
4. `snapshots.start: '2019-01-13 22:00'`, `snapshots.end: '2019-01-20 22:00'`, `snapshots.inclusive: 'left'`
5. `clustering.temporal.resolution_elec: false` (hourly)
6. `atlite.default_cutout: europe-2019-era5` and matching `atlite.cutouts.europe-2019-era5` block
7. `electricity.extendable_carriers.Generator/StorageUnit/Store/Link: []`
8. `lines.max_extension: 500`, `links.max_extension: 500`
9. `solving.options.load_shedding: 100000` (EUR/MWh)
10. `electricity.renewable_carriers` includes hydro (`hydro` present)

Add `stress_test` section only in stress config:
1. `enable: true`
2. `country: RO`
3. `load_factor_full_window: 1.12`
4. `hydro_factor_full_window: 0.60`
5. `gas_factor_first_72h: 0.70`
6. `scada.tight_hours: 24`, `scada.relaxed_hours: 48`
7. `scada.ramp_tight_per_hour: 0.10`, `scada.ramp_relaxed_per_hour: 0.25`
8. `import_cap.zero_hours: 48`, `import_cap.half_hours: 48`, `import_cap.half_factor: 0.5`

---

### 2) Shock Logic Module (`scripts/romania_winter_stress.py`)

Implement pure functions:

1. `apply_timeseries_shocks(n, snapshots, cfg)`  
   Applies pre-model series changes:
   - Load shock: multiply `n.loads_t.p_set` for RO loads by `1.12` over all 168h.
   - Hydro shock: for RO hydro generators (`ror`, `hydro`) scale `p_max_pu` by `0.60`; for RO hydro storage (`hydro`, `PHS`) scale inflow (and storage dispatch availability if present) by `0.60`.
   - Gas shock: for RO gas generators (`OCGT`, `CCGT`) scale `p_max_pu` by `0.70` for first 72h only.
   - Add validation logs if expected components are absent.

2. `add_scada_proxy_constraints(n, snapshots, cfg)`  
   Adds linear ramp constraints on RO controllable generators:
   - Hours 1-24: `|p_t - p_{t-1}| <= 0.10 * p_nom_effective`
   - Hours 25-72: `|p_t - p_{t-1}| <= 0.25 * p_nom_effective`
   - `p_nom_effective` uses decision variable for extendables, static value for fixed assets.

3. `add_import_cap_constraints(n, snapshots, cfg)`  
   Adds directional constraints on RO border interconnectors:
   - First 48h: inbound cap = 0% of line/link capacity.
   - Next 48h: inbound cap = 50% of line/link capacity.
   - Remaining 72h: no additional import cap.
   - Apply to both AC lines (`Line-s`) and links (`Link-p`) with orientation-aware sign.
   - If no RO border assets exist, log and expose flag for reporting fallback note.

---

### 3) Integrate With Solver (`scripts/solve_network.py`)

1. Import functions from `scripts/romania_winter_stress.py`.
2. In `prepare_network(...)`, after snapshot clipping and before model creation:
   - If `config.get("stress_test", {}).get("enable")`, call `apply_timeseries_shocks(...)`.
3. In `extra_functionality(...)`:
   - If stress enabled, call `add_scada_proxy_constraints(...)` then `add_import_cap_constraints(...)`.
4. Keep behavior unchanged when `stress_test.enable` is false or absent.

---

### 4) Reporting & Deliverables (`scripts/report_romania_winter_stress.py`)

CLI inputs:
1. `--baseline-net`
2. `--scenario-net`
3. `--country RO`
4. `--outdir results/romania-2019-winter-stress-comparison`

Generate CSVs:
1. `ens_summary.csv` with ENS MWh, shedding hours, max shedding MW.
2. `system_cost_comparison.csv` with baseline cost, scenario cost, delta absolute and percent.
3. `daily_net_imports_mwh.csv` (baseline/scenario) aggregated by day.
4. `interconnector_flow_congestion.csv` with mean/p95/max loading and congested hours.
5. `generation_mix_mwh.csv` by technology and case.
6. `curtailment_mwh.csv` by technology and case.
7. `lmp_summary_ro.csv` with mean, p95, max (optional, always attempted).

Generate figures in both PNG and PDF:
1. `fig_01_shedding_timeseries.(png|pdf)`
2. `fig_02_daily_net_imports.(png|pdf)`
3. `fig_03_generation_mix.(png|pdf)`
4. `fig_04_interconnector_loading.(png|pdf)`
5. `fig_05_ro_price_distribution.(png|pdf)` if LMP available.

Generate 1-page note:
1. `assumptions_limitations.md`  
   Must include exact dates, SCADA proxy formula, import-constraint formulation, fallback behavior if missing interconnectors, and interpretation limits.

Implementation detail for daily aggregation:
1. Treat snapshots as UTC.
2. Convert to `Europe/Bucharest` for daily MWh/day grouping to align with local-window reporting.

---

### 5) Run Orchestration (`run_romania_winter_stress.py`)

Implement a single script that:
1. Unlocks Snakemake for baseline config.
2. Solves baseline target `results/romania-2019-winter-baseline/networks/base_s_10_elec_.nc`.
3. Unlocks Snakemake for stress config.
4. Solves stress target `results/romania-2019-winter-stress/networks/base_s_10_elec_.nc`.
5. Runs `scripts/report_romania_winter_stress.py`.
6. Prints output paths for all deliverables.

Use `conda run -n pypsa-eur ...` in this repo (detected env naming).

---

### 6) Tests (`test/test_romania_winter_stress.py`)

Add unit tests on synthetic tiny networks:
1. `test_apply_timeseries_shocks_windows`  
   Verifies +12% load full window, hydro 60% full window, gas 70% first 72h only.
2. `test_scada_constraints_created`  
   Verifies constraint names exist and are indexed over expected snapshot ranges.
3. `test_import_constraints_directional`  
   Verifies inbound RO caps for both line orientations and links.
4. `test_stress_disabled_no_changes`  
   Verifies no-op path.

No full optimization run in tests.

---

### 7) Acceptance Criteria

1. Baseline and stress scenarios both solve for exactly 168 hourly snapshots.
2. Stress run applies all five requested shocks with exact hour windows.
3. Load shedding exists as explicit high-penalty carrier and ENS metrics are non-null.
4. Comparison output folder contains all required CSVs and PNG/PDF figures.
5. 1-page assumptions/limitations note exists and documents SCADA proxy and limitations.
6. Unit tests for shock and constraint logic pass.

---

### Public Interfaces / Schema Additions

1. New config block: `stress_test`
2. New script CLI: `scripts/report_romania_winter_stress.py --baseline-net ... --scenario-net ... --country ... --outdir ...`
3. New runner script: `run_romania_winter_stress.py`

---

### Assumptions And Defaults Locked

1. UTC snapshot window is used in config: `2019-01-13 22:00` to `2019-01-20 22:00` (`inclusive: left`).
2. Local EET interpretation is `2019-01-14 00:00` to `2019-01-21 00:00`.
3. Country set is exactly `[RO, BG, HU, RS]`.
4. Hybrid mode means no generation/storage expansion and limited grid expansion (`+500 MW` per asset).
5. SCADA proxy uses moderate levels (`10%/h`, then `25%/h`).
6. If 2019 cutout is missing locally, workflow retrieves `europe-2019-era5` from configured archive source.
