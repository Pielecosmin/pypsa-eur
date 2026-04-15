# Year-Specific YAML Template Architecture

## Overview

The scenario manager now supports **intelligent template selection** based on the chosen cutout year. When you select 2023 from the UI dropdown, the system automatically loads the 2023-specific YAML template with pre-configured settings optimized for 2023 weather data.

## Template Files

### Primary Templates

| Template File | Purpose | Used When |
|---|---|---|
| `scenario_template.yaml` | Default template for 2020 cutout year | Cutout year = 2020 (default) |
| `scenario_template_2023.yaml` | Optimized template for 2023 cutout year | Cutout year = 2023 |

Both templates reside in: `1_piele_docs/`

### Template Selection Logic

```
User selects cutout_year from UI dropdown
        ↓
build_working_config() or build_configs() called with ScenarioInputs
        ↓
resolve_template_path(template_path, inputs.cutout_year)
        ↓
If cutout_year == "2020" → Use scenario_template.yaml (default)
If cutout_year == "2023" → Use scenario_template_2023.yaml (if exists, else default)
        ↓
load_template(resolved_path)
        ↓
Configuration applied with year-appropriate defaults
```

## Configuration Differences

### scenario_template.yaml (2020)
```yaml
snapshots:
  start: "2020-12-01"
  end: "2020-12-08"

electricity:
  estimate_renewable_capacities:
    year: 2020

atlite:
  default_cutout: europe-2020-sarah3-era5
```

### scenario_template_2023.yaml (2023)
```yaml
snapshots:
  start: "2023-01-15"
  end: "2023-01-22"

electricity:
  estimate_renewable_capacities:
    year: 2023

atlite:
  default_cutout: europe-2023-sarah3-era5
```

## How It Works

### Step-by-Step Flow

1. **User Opens Scenario Manager UI**
   - Loads default template path: `1_piele_docs/scenario_template.yaml`

2. **User Selects Cutout Year**
   - Dropdown shows: [2020, 2023]
   - Selection stored in `cutout_year` StringVar

3. **User Provides Scenario Details**
   - Sets all other parameters (clusters, solver, countries, stress parameters, etc.)

4. **User Clicks "Build Config" or "Enqueue Run"**
   - Calls `build_working_config()` or `build_configs()`
   - Passes `inputs.cutout_year` to function

5. **System Resolves Template Path**
   - Calls `resolve_template_path(template_path, inputs.cutout_year)`
   - Logic:
     ```python
     if cutout_year == "2020":
         return base_template_path  # scenario_template.yaml
     elif cutout_year == "2023":
         year_specific = parent_dir / "scenario_template_2023.yaml"
         if year_specific.exists():
             return year_specific
         return base_template_path  # Fallback if not found
     ```

6. **System Loads Selected Template**
   - `load_template()` reads YAML from resolved path
   - Returns configuration dictionary

7. **Configuration Applied**
   - User inputs merged with template defaults
   - Cutout year validated and applied via `_apply_cutout_to_config()`
   - Generated config has correct settings for chosen year

8. **Run Execution**
   - Generated config sent to Snakemake
   - Snakemake uses europe-20XX-sarah3-era5 cutout file

## Implementation Details

### resolve_template_path() Function

Location: `1_piele_dashboard/scenario_manager/config_builder.py`

```python
def resolve_template_path(base_template_path: Path, cutout_year: str = "2020") -> Path:
    """Resolve template path based on cutout year.
    
    Intelligently selects year-specific templates:
    - If cutout_year = "2023", looks for scenario_template_2023.yaml
    - If cutout_year = "2020", uses default scenario_template.yaml
    - Falls back to base template if year-specific not found
    
    Args:
        base_template_path: Path to default template (e.g., scenario_template.yaml)
        cutout_year: Year as string ("2020" or "2023")
    
    Returns:
        Path to the template file to use
    """
```

### Integration Points

1. **build_working_config()** (Line ~360)
   ```python
   resolved_template_path = resolve_template_path(template_path, inputs.cutout_year)
   template_cfg = load_template(resolved_template_path)
   ```

2. **build_configs()** (Line ~390)
   ```python
   resolved_template_path = resolve_template_path(template_path, inputs.cutout_year)
   template_cfg = load_template(resolved_template_path)
   ```

## Why Year-Specific Templates?

### Advantages

✅ **Appropriate Defaults** - Each year gets realistic default snapshot dates
✅ **Correct Electricity Year** - Renewable capacity estimates use matching year
✅ **Pre-Configured Cutouts** - Cutout name set correctly from the start
✅ **Flexibility** - Easy to add 2024, 2025, etc. in future
✅ **Clarity** - Users understand they're working with year-consistent data
✅ **Fallback Safety** - Missing year-specific template falls back gracefully

### Example Scenario

**User creates 2023 winter stress scenario:**

```
1. Selects "Cutout year: 2023"
2. System auto-selects scenario_template_2023.yaml
3. Template has:
   - snapshots: 2023-01-15 to 2023-01-22 (2023 winter baseline)
   - electricity.year: 2023 (correct for capacity estimates)
   - atlite.default_cutout: europe-2023-sarah3-era5 (correct weather file)
4. User accepts or overrides these defaults as needed
5. Config generated with year-consistent values
6. Simulation runs with 2023 weather data
```

## Adding New Year Templates

To add support for year 2024 or later:

### 1. Create Template File
```bash
cp 1_piele_docs/scenario_template_2023.yaml 1_piele_docs/scenario_template_2024.yaml
```

### 2. Update Contents
```yaml
snapshots:
  start: "2024-01-15"  # Update to 2024 dates
  end: "2024-01-22"

electricity:
  estimate_renewable_capacities:
    year: 2024  # Update year

atlite:
  default_cutout: europe-2024-sarah3-era5  # Update cutout name
  cutouts:
    europe-2024-sarah3-era5:
      time:
        - "2024"
        - "2024"
```

### 3. Update UI Dropdown
```python
# scenario_manager_ui.py, line ~133
("cutout_year", self.cutout_year, ["2020", "2023", "2024"]),
```

### 4. Ensure Cutout File Exists
```bash
# Must have: data/cutout/archive/v0.8/europe-2024-sarah3-era5.nc
```

### 5. Update Template Validation (Optional)
```python
# config_builder.py, _apply_cutout_to_config()
if cutout_year not in ("2020", "2023", "2024"):
    raise ValueError(...)
```

That's it! The `resolve_template_path()` function will automatically detect and use `scenario_template_2024.yaml`.

## Debugging Template Issues

### Template Not Found
If system falls back to default template:
```bash
# Check file exists
ls -la 1_piele_docs/scenario_template_2023.yaml

# Check file permissions (must be readable)
chmod 644 1_piele_docs/scenario_template_2023.yaml
```

### Wrong Template Loaded
Add debug logging to verify:
```python
# In config_builder.py
import logging
logger = logging.getLogger(__name__)

def resolve_template_path(...):
    resolved = ...
    logger.info(f"Using template: {resolved}")
    return resolved
```

### Snapshot Dates Wrong
If defaults are not from selected year:
- Check `scenario_template_2023.yaml` has correct snapshots section
- Verify YAML syntax is valid: `yamllint 1_piele_docs/scenario_template_2023.yaml`

## File Locations

```
pypsa-eur/
├── 1_piele_dashboard/
│   ├── scenario_manager_ui.py          # UI dropdown (lines ~60, ~133)
│   └── scenario_manager/
│       └── config_builder.py            # resolve_template_path() function
├── 1_piele_docs/
│   ├── scenario_template.yaml           # Default (2020)
│   ├── scenario_template_2023.yaml      # Year-specific (2023)
│   └── CUTOUT_CONFIG.md                 # User documentation
└── data/
    └── cutout/archive/v0.8/
        ├── europe-2020-sarah3-era5.nc
        └── europe-2023-sarah3-era5.nc
```

## Best Practices

1. **Keep Templates Synchronized**
   - Both templates should have identical structure
   - Only differences: year values, snapshot dates, cutout names

2. **Validate YAML Syntax**
   ```bash
   python -c "import yaml; yaml.safe_load(open('scenario_template_2023.yaml'))"
   ```

3. **Version Control**
   - Track both template files in git
   - Document any customizations

4. **Test New Templates**
   - Create test scenario with new template
   - Verify cutout year, snapshot dates, electricity year match
   - Check generated config before running Snakemake

5. **Fallback Planning**
   - Always keep default `scenario_template.yaml`
   - Year-specific templates should be optional enhancement
   - Missing template gracefully falls back to default

## Technical Architecture

```
UI Layer
  ↓
build_working_config(inputs, template_path)
  ↓
resolve_template_path(template_path, inputs.cutout_year)
  ├─ 2020 → scenario_template.yaml
  └─ 2023 → scenario_template_2023.yaml (if exists)
  ↓
load_template(resolved_path)
  ↓
_base_config_from_inputs(template_cfg, working_yaml)
  ↓
_apply_inputs_to_config(...)
  ↓
_apply_cutout_to_config(...)
  ↓
Generated YAML written to config/adversarial/generated/
```

## Support & Troubleshooting

For issues with year-specific templates:
1. Verify both template files exist and are readable
2. Check template YAML syntax: `yamllint scenario_template_*.yaml`
3. Verify cutout files exist: `ls data/cutout/archive/v0.8/europe-*.nc`
4. Check UI dropdown has year option selected
5. Verify generated config has correct cutout name and snapshot dates
6. See CUTOUT_CONFIG.md for user-level troubleshooting

---

**Implementation Date:** January 24, 2025  
**Version:** 1.0  
**Status:** Production Ready
