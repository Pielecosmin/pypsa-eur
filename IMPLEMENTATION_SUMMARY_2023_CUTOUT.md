# 2023 Cutout Data Support - Implementation Summary

**Date Completed:** 2025-01-24  
**Feature:** Support for 2023 weather data alongside existing 2020 cutout  
**Status:** ✅ COMPLETE

## Overview

Successfully implemented multi-year cutout support in the PyPSA-EUR scenario manager. Users can now select between 2020 (default) and 2023 weather data for energy system simulations via a new UI dropdown with automatic date validation.

## Changes Made

### 1. **Data Type Enhancement** (`types.py`)
- **File:** `1_piele_dashboard/scenario_manager/types.py`
- **Change:** Added `cutout_year: str = "2020"` field to `ScenarioInputs` dataclass (line 42)
- **Impact:** All scenario configurations can now specify which cutout year to use
- **Backward Compatible:** Default is 2020 for existing workflows

### 2. **Template Configuration** (`scenario_template.yaml`)
- **File:** `1_piele_docs/scenario_template.yaml`
- **Change:** Expanded `atlite.cutouts` section with 2023 definition (lines 65-77)
- **Configuration Added:**
  ```yaml
  europe-2023-sarah3-era5:
    module: era5
    x: [-12.0, 35.0]
    y: [33.0, 72.0]
    dx: 0.3
    dy: 0.3
    time: ["2023", "2023"]
  ```
- **Impact:** Both 2020 and 2023 cutout definitions available for selection

### 3. **Config Builder Enhancement** (`config_builder.py`)
- **File:** `1_piele_dashboard/scenario_manager/config_builder.py`
- **New Function:** `_apply_cutout_to_config()` (lines 116-171)
  - Validates cutout year is 2020 or 2023
  - Selects correct cutout name dynamically
  - Validates snapshot dates match selected year
  - Raises clear error messages for mismatches
  - Optional date validation to catch user errors
- **Integration:** Called automatically after config creation (lines 374-375, 382-383)
- **Impact:** Automatic cutout selection and date validation at build time

### 4. **UI Enhancement** (`scenario_manager_ui.py`)
- **File:** `1_piele_dashboard/scenario_manager_ui.py`
- **Changes:**
  1. **Variable Addition** (line 60): `self.cutout_year = tk.StringVar(value=...)`
  2. **Form Field** (line 133): Added dropdown to builder form with values ["2020", "2023"]
  3. **Label Translation** (line 318): Added "cutout_year" to i18n label map
  4. **UI State Persistence** (line 707): Saves cutout_year to session state
  5. **ScenarioInputs** (line 387): Passes cutout_year from UI to config builder

- **UX Flow:**
  1. User opens Scenario Builder tab
  2. Selects cutout year (2020 or 2023) from dropdown
  3. Enters snapshot dates matching the year
  4. Builds config - validation catches date mismatches
  5. Selection persisted across sessions

### 5. **Internationalization** (`i18n.py`)
- **File:** `1_piele_dashboard/scenario_manager/i18n.py`
- **Changes:**
  - English: `"cutout_year": "Cutout year"` (line 28)
  - Romanian: `"cutout_year": "Anul cutout"` (line 82)
- **Impact:** UI label displays in both languages

### 6. **Documentation** (`CUTOUT_CONFIG.md`)
- **File:** `1_piele_docs/CUTOUT_CONFIG.md` (NEW - 256 lines)
- **Contents:**
  - Overview of supported cutout years
  - UI usage instructions
  - Configuration file reference
  - Validation rules and error handling
  - Troubleshooting guide
  - Programmatic usage examples
  - Best practices
  - Future expansion guidelines

## Technical Implementation Details

### Validation Pipeline

```
User Selects → UI StringVar (cutout_year) → _collect_inputs() → ScenarioInputs → 
build_configs() → _apply_inputs_to_config() → _apply_cutout_to_config() → 
Validation & Config Modification → Generated YAML
```

### Error Handling

1. **Invalid Year:** 
   ```
   ValueError: "Unsupported cutout year: YYYY. Must be 2020 or 2023."
   ```

2. **Missing Definition:**
   ```
   ValueError: "Cutout [name] not defined in template. Make sure template has..."
   ```

3. **Date Mismatch:**
   ```
   ValueError: "Snapshot dates don't match cutout year 2020: got 2023-12-01 to..."
   ```

### Backward Compatibility

- ✅ Default cutout year: 2020
- ✅ Existing configs auto-default to 2020
- ✅ No breaking changes to existing workflows
- ✅ Old scenario templates still work
- ✅ State file migration handles missing field automatically

## File Modifications Summary

| File | Lines Changed | Type | Impact |
|------|--------------|------|--------|
| types.py | 1 addition | Data Model | Core infrastructure |
| scenario_template.yaml | 12 additions | Configuration | Template data |
| config_builder.py | 56 additions, 6 modifications | Business Logic | Validation & selection |
| scenario_manager_ui.py | 10 additions, 5 modifications | UI/UX | User interface |
| i18n.py | 2 additions | Localization | Language support |
| CUTOUT_CONFIG.md | 256 lines | Documentation | User guide |

**Total Lines Added:** ~285  
**Total Files Modified:** 5  
**Total Files Created:** 1  
**Backwards Compatible:** ✅ Yes  
**Syntax Errors:** ✅ None (all files verified)

## Testing Checklist

- [x] Type definitions compile
- [x] Config builder functions defined correctly
- [x] UI variables initialized properly
- [x] Form control added to builder
- [x] Translation keys present in i18n
- [x] State persistence includes cutout_year
- [x] Documentation complete
- [ ] Test 2020 scenario creation (manual)
- [ ] Test 2023 scenario creation (manual)
- [ ] Test date validation enforcement (manual)
- [ ] Test UI persistence across sessions (manual)

## Usage Example

### Via UI

1. Open Scenario Manager
2. In Builder tab, set:
   - Output name: "romania-2023-test"
   - Snapshot start: "2023-01-15"
   - Snapshot end: "2023-01-22"
   - **Cutout year: "2023"** (NEW dropdown)
   - Other parameters as needed
3. Click "Enqueue run"

### Via Configuration File

```yaml
# scenario_config.yaml
atlite:
  default_cutout: "europe-2023-sarah3-era5"

run:
  snapshots:
    start: "2023-01-15"
    end: "2023-01-22"
```

### Programmatically

```python
inputs = ScenarioInputs(
    ...
    snapshot_start="2023-01-15",
    snapshot_end="2023-01-22",
    cutout_year="2023",
    ...
)
```

## Data Files Required

- ✅ `data/cutout/archive/v0.8/europe-2020-sarah3-era5.nc` (existing)
- ✅ `data/cutout/archive/v0.8/europe-2023-sarah3-era5.nc` (must be present)

**Note:** Download 2023 cutout if missing:
```bash
python download_cutout.py --year 2023
```

## Deployment Notes

### For Existing Users

1. Pull latest changes
2. No migration needed (defaults to 2020)
3. Existing projects continue to work unchanged
4. Optional: Upgrade to use 2023 cutout

### For New Users

1. Clone repository
2. Ensure both cutout files present in `data/cutout/archive/v0.8/`
3. Open Scenario Manager UI - cutout_year dropdown ready to use

## Future Enhancements

This implementation easily supports:
- Adding 2024, 2025, etc. years (just add YAML + update dropdown)
- Custom date range validation per year
- Cutout data quality metrics display
- Automated cutout availability checking
- Weather data year metadata in results

## Key Features Delivered

✅ **Multi-Year Support** - 2020 and 2023 weather data  
✅ **User-Friendly** - Dropdown selection in UI  
✅ **Validation** - Automatic date-year matching  
✅ **Backward Compatible** - 2020 is default  
✅ **Documented** - Comprehensive guide included  
✅ **Internationalized** - English and Romanian  
✅ **Persistent** - Selection saved between sessions  
✅ **Error Handling** - Clear validation messages  

## Integration Status

- ✅ Code implemented
- ✅ Syntax verified
- ✅ Documentation complete
- ✅ Backward compatibility maintained
- ✅ No external dependencies added
- Ready for testing & deployment

## Notes

- All existing scenarios default to 2020 cutout
- UI dropdown remembers selection via state_store.json
- Validation occurs at config build time (early error detection)
- Both cutout YAML definitions always available (transparent selection)
- Date validation is optional but recommended feature
- Code follows existing project patterns and style

---

**Implementation By:** GitHub Copilot  
**Status:** Ready for Integration Testing  
**Next Steps:** Manual testing of 2020/2023 scenarios, then production deployment
