# Cutout Year Configuration Guide

## Overview

The PyPSA-EUR scenario manager now supports multiple years of weather data (cutout files) for simulations. This allows you to run energy system analyses using different years of weather conditions.

## Supported Cutout Years

- **2020** (Default) - Original cutout used for all existing scenarios
  - File: `data/cutout/archive/v0.8/europe-2020-sarah3-era5.nc`
  - Template: `1_piele_docs/scenario_template.yaml`
  - Default snapshots: 2020-12-01 to 2020-12-08 (winter stress period)
  - ERA5 reanalysis + SARAH-3 satellite radiation data

- **2023** (New) - Additional year for comparison and stress testing
  - File: `data/cutout/archive/v0.8/europe-2023-sarah3-era5.nc`
  - Template: `1_piele_docs/scenario_template_2023.yaml` (auto-selected when 2023 cutout year chosen)
  - Default snapshots: 2023-01-15 to 2023-01-22 (winter stress period)
  - ERA5 reanalysis + SARAH-3 satellite radiation data

## How to Use

### Via Scenario Manager UI

1. **Open the Scenario Builder tab**
2. **Fill in scenario parameters as usual** (output name, countries, clusters, solver, etc.)
3. **Set Snapshot Dates** - Enter the date range for your simulation
   - Example: `2020-12-01` to `2020-12-08` (for 2020 cutout)
   - Example: `2023-01-15` to `2023-01-22` (for 2023 cutout)
4. **Select Cutout Year** - New dropdown field:
   - Choose `2020` (default) or `2023`
   - The year should match your snapshot dates
5. **Configure Stress Parameters** (if needed)
6. **Click "Enqueue run"** to start the simulation

### Intelligent Template Selection

The system **automatically selects the appropriate YAML template** based on your cutout year choice:

- **Select 2020 cutout** → Uses `1_piele_docs/scenario_template.yaml`
  - Default snapshots: 2020-12-01 to 2020-12-08
  - Electricity year: 2020

- **Select 2023 cutout** → Uses `1_piele_docs/scenario_template_2023.yaml`
  - Default snapshots: 2023-01-15 to 2023-01-22
  - Electricity year: 2023
  - Pre-configured with 2023 weather data

**You don't need to manually select templates** – the system handles it for you based on the cutout year dropdown selection.

### Via Configuration File

If you prefer direct YAML configuration:

```yaml
atlite:
  default_cutout: "europe-2020-sarah3-era5"  # or "europe-2023-sarah3-era5"
```

Both cutout definitions are available in `1_piele_docs/scenario_template.yaml`:

```yaml
atlite:
  default_cutout: europe-2020-sarah3-era5
  cutouts:
    europe-2020-sarah3-era5:
      module: era5
      x: [-12.0, 35.0]
      y: [33.0, 72.0]
      dx: 0.3
      dy: 0.3
      time: ["2020", "2020"]
    
    europe-2023-sarah3-era5:
      module: era5
      x: [-12.0, 35.0]
      y: [33.0, 72.0]
      dx: 0.3
      dy: 0.3
      time: ["2023", "2023"]
```

## Important Validation Rules

### Date-Year Matching

The system validates that your snapshot dates match the selected cutout year:

✅ **Valid combinations:**
- Cutout Year: 2020, Dates: 2020-12-01 to 2020-12-08
- Cutout Year: 2023, Dates: 2023-01-15 to 2023-01-22

❌ **Invalid combinations (will error):**
- Cutout Year: 2020, Dates: 2023-12-01 to 2023-12-08
- Cutout Year: 2023, Dates: 2020-01-15 to 2020-01-22

**Error message if mismatch:** 
```
Snapshot dates don't match cutout year 2020: got 2023-12-01 to 2023-12-08.
Cutout year must match snapshot year.
```

### Supported Snapshot Ranges

**For 2020 cutout:**
- All dates within 2020 (January 1 - December 31, 2020)
- Minimum recommended: 3-7 days for testing
- Common usage: 7-14 day winter stress periods

**For 2023 cutout:**
- All dates within 2023 (January 1 - December 31, 2023)
- Same flexibility as 2020

## Default Behavior

- **Default cutout year:** 2020 (backward compatible with existing workflows)
- **UI dropdown:** Remembers your last selection between sessions
- **Recommendation:** Use 2020 for baseline runs, compare with 2023 for climate sensitivity analysis

## Troubleshooting

### Error: "Unsupported cutout year: 20XX"
- Ensure you select only 2020 or 2023 from the dropdown
- Other years are not currently available

### Error: "Snapshot dates don't match cutout year"
- Check that your snapshot start/end dates match the selected year
- Example: If you select 2023, use dates like 2023-MM-DD, not 2020-MM-DD

### Error: "Cutout X not defined in template"
- Verify `1_piele_docs/scenario_template.yaml` contains both cutout definitions
- Ensure the template file hasn't been modified or corrupted

### File not found: "europe-2023-sarah3-era5.nc"
- Verify the cutout file exists at: `data/cutout/archive/v0.8/europe-2023-sarah3-era5.nc`
- If missing, download it via `python download_cutout.py --year 2023`

## Programmatic Usage

When building scenarios programmatically:

```python
from scenario_manager.types import ScenarioInputs

inputs = ScenarioInputs(
    run_mode="paired",
    output_name="scenario-2023-comparison",
    scenario_slug="romania-winter-2023",
    country="RO",
    countries=["RO", "BG", "HU", "RS"],
    snapshot_start="2023-01-15",
    snapshot_end="2023-01-22",
    clusters=10,
    solver_name="highs",
    solver_options="highs-simplex",
    cutout_year="2023",  # NEW: Specify cutout year
    stress_enable=True,
    # ... stress parameters
)

from scenario_manager.config_builder import build_configs

result = build_configs(
    repo_root=Path("."),
    inputs=inputs,
    template_path=Path("1_piele_docs/scenario_template.yaml")
)
```

## Configuration Pipeline

1. **User Input (UI)** → cutout_year selected from dropdown
2. **Validation** → Year must be 2020 or 2023
3. **ScenarioInputs** → cutout_year stored in dataclass
4. **Config Builder** → `_apply_cutout_to_config()` function processes year
5. **Date Validation** → Snapshot dates checked against year
6. **Config Generation** → Correct cutout name set in generated YAML
7. **Snakemake Execution** → Uses specified cutout for weather data

## File Locations

```
pypsa-eur/
├── 1_piele_dashboard/
│   ├── scenario_manager_ui.py          # UI with cutout_year dropdown
│   ├── scenario_manager/
│   │   ├── types.py                    # ScenarioInputs dataclass
│   │   ├── config_builder.py           # _apply_cutout_to_config() function
│   │   └── i18n.py                     # English/Romanian labels
│   └── scenario_manager_state.json     # Persisted UI state (includes cutout_year)
├── 1_piele_docs/
│   └── scenario_template.yaml          # Cutout definitions for both years
└── data/
    └── cutout/
        └── archive/
            └── v0.8/
                ├── europe-2020-sarah3-era5.nc  # 2020 cutout file
                └── europe-2023-sarah3-era5.nc  # 2023 cutout file
```

## Best Practices

1. **Backward Compatibility** - Always use 2020 cutout for baseline/reference scenarios
2. **Comparison Studies** - Run same scenario with both 2020 and 2023 cutouts to assess climate variations
3. **Stress Testing** - Use 2023 data for updated extreme weather scenarios
4. **Documentation** - Always record which cutout year was used in results metadata
5. **Reproducibility** - Document the exact start/end dates used in each scenario

## Adding New Cutout Years (Future)

To support additional years (2024, 2025, etc.):

1. Download cutout file: `europe-YYYY-sarah3-era5.nc`
2. Place in: `data/cutout/archive/v0.8/`
3. Update `scenario_template.yaml`:
   ```yaml
   europe-YYYY-sarah3-era5:
     module: era5
     x: [-12.0, 35.0]
     y: [33.0, 72.0]
     dx: 0.3
     dy: 0.3
     time: ["YYYY", "YYYY"]
   ```
4. Update UI dropdown in `scenario_manager_ui.py` line 133:
   ```python
   ("cutout_year", self.cutout_year, ["2020", "2023", "YYYY"]),
   ```
5. Config builder validation will automatically work for new years

## Support

For issues or questions:
- Check scenario logs in `logs/planui/`
- Verify template YAML syntax
- Ensure snapshot dates are in YYYY-MM-DD format
- Contact: [project maintainers]
