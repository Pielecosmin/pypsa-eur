# 📥 Data Download - External Data Acquisition

Utilities for downloading required datasets from external sources. PyPSA-Eur needs environmental and geographic data for simulations.

## Data Download Scripts

### **download_cutout.py**
Downloads atmospheric/weather data cutouts for renewable energy profiles.

**Purpose:**
- Fetch ERA5 reanalysis data
- Download SARAH solar radiation data
- Extract cutouts for simulation region

**Data Downloaded:**
```
Cutout: europe-2020-sarah3-era5.nc
├── Solar irradiance (SARAH-3)
├── Wind speed (ERA5)
├── Temperature (ERA5)
├── Runoff/precipitation (ERA5)
└── Other meteorological variables
```

**Data Source:** 
- ERA5: Copernicus Climate Data Store
- SARAH-3: Satellite-based radiation data

**How to Run:**
```bash
python download_cutout.py
```

**Output:**
```
data/cutout/
├── archive/
│   └── v0.8/europe-2020-sarah3-era5.nc     (1.2 GB)
└── europe-2020-sarah3-era5.nc (symlink)
```

**Time Required:** 10-30 minutes (internet dependent)

**Storage:** ~1.2 GB (compressed netCDF format)

---

### **download_zenodo_files.py**
Downloads pre-processed datasets and benchmarks from Zenodo repository.

**Purpose:**
- Fetch power plant datasets
- Download preprocessed transmission networks
- Get cost data and technology specifications
- Retrieve benchmark configurations

**Data Downloaded:**
```
Power Plant Data
├── powerplants.csv          (Generator locations/capacities)
└── refineries.csv           (Industrial facility data)

Network Data
├── transmission_projects/   (Future expansion plans)
├── osm_boundaries/          (Geographic boundaries)
└── natura_sites/            (Environmental protections)

Cost Data
├── costs_2050.csv           (Technology cost projections)
└── parameter_corrections/   (Regional adjustments)

Benchmark Data
├── tutorial_configs/        (Example scenarios)
└── validation_datasets/     (Validation data)
```

**Data Source:** Zenodo.org (PyPSA-Eur community repository)

**How to Run:**
```bash
python download_zenodo_files.py
```

**Output:**
```
data/
├── powerplants/
│   └── primary/0.7.1/powerplants.csv
├── costs/
│   └── primary/v0.13.3/costs_2050.csv
├── entsoegridkit/
├── osm_boundaries/
└── ... (other datasets)
```

**Time Required:** 30 minutes - 2 hours (varies by dataset size and internet)

**Storage:** ~5-10 GB total for all datasets

---

## Data Organization

After successful download, data is organized as:

```
data/
├── corine/                    # Land cover data
├── costs/                     # Technology costs
│   └── primary/v0.13.3/costs_2050.csv
├── cutout/                    # Weather/atmospheric data
│   └── europe-2020-sarah3-era5.nc (1.2GB)
├── entsoegridkit/            # European grid data (ENTSOE)
├── eez/                      # Exclusive economic zones
├── eu_nuts2021/              # Regional boundaries
├── existing_infrastructure/  # Current power plants
├── gdp_per_capita/           # Economic data
├── jrc_ardeco/               # Industrial data
├── luisa_land_cover/         # High-res land cover
├── natura/                   # Protected areas
├── osm/                      # OpenStreetMap data
├── osm_boundaries/           # Geographic boundaries
├── population_count/         # Population distribution
├── powerplants/              # Generator database
│   └── primary/0.7.1/powerplants.csv
├── retro/                    # Building retrofit data
├── ship_raster/              # Shipping routes
└── synthetic_electricity_demand/  # Demand profiles
```

---

## Download Workflow

**First-Time Setup:**
```
1. Download cutout (weather data)
   python download_cutout.py

2. Download Zenodo datasets
   python download_zenodo_files.py

3. Verify downloads (see ../diagnostics/check_csv.py)
   python ../diagnostics/check_csv.py

4. Ready for scenario execution
   python ../runners/run_baseline_only.bat
```

**Subsequent Runs:**
- Datasets are cached locally
- Only run if missing data error appears
- Pre-downloaded data is reused

---

## Data Requirements Summary

| Dataset | Size | Time | Required? |
|---------|------|------|-----------|
| Cutout (Weather) | 1.2 GB | 10-30 min | ✅ YES |
| Power Plants | 50 MB | <5 min | ✅ YES |
| Costs | 30 MB | <5 min | ✅ YES |
| Boundaries | 200 MB | 5-10 min | ✅ YES |
| OSM Grid | 500 MB | 10-20 min | ✅ YES |
| ENTSOE Grid | 100 MB | 5 min | ✅ YES |
| Natura/EEZ | 100 MB | 5 min | ⚠️ Optional |
| CORINE Land | 300 MB | 10-15 min | ⚠️ Optional |

**Minimum Install:** ~2.5 GB (11000 required datasets)
**Full Install:** ~10 GB (all datasets)

---

## Troubleshooting Download Issues

### Issue: Download fails due to network error
```bash
# Retry download
python download_cutout.py  # Automatic retry built-in

# Check internet connectivity
ping www.copernicus-climate.eu
```

### Issue: Out of disk space
```bash
# Check current disk usage
dir data/ | measure-object -Sum Length

# Download individually
python download_cutout.py      # Required first
python download_zenodo_files.py  # Optional later
```

### Issue: Timeout downloading large files
```bash
# Increase timeout (modify script):
# timeout = 3600  # seconds (1 hour)

# Or download manually from:
# - CDS: https://cds.climate.copernicus.eu/
# - Zenodo: https://zenodo.org/search?q=pypsa-eur
```

### Issue: Incomplete download detected
```bash
# Delete corrupted file and retry
rm data/cutout/europe-2020-sarah3-era5.nc
python download_cutout.py
```

---

## Data Caching & Reuse

Downloaded data is automatically cached in `data/` folder:
- Future scenario runs reuse existing data
- No re-downloading unless explicitly deleted
- Archive versions kept for reproducibility

**Archive locations:**
```
data/cutout/archive/v0.8/
data/costs/primary/v0.13.3/
data/powerplants/primary/0.7.1/
```

---

## Integration with Workflow

```
1. Data Download (this folder)
   download_cutout.py
   download_zenodo_files.py
          ↓
2. Diagnostics (validate)
   check_csv.py
   check_url.py
          ↓
3. Scenario Configuration
   config/*.yaml
          ↓
4. Run Simulations (runners/)
   run_baseline_only.bat
   run_all_scenarios.py
          ↓
5. Analyze Results (analysis/)
          ↓
6. Visualize (dashboard/)
   visualize_scenarios_ui_v2.py
```

---

## File Organization

```
data_download/
├── download_cutout.py              # Download weather data
└── download_zenodo_files.py        # Download general datasets
```

---

## Data Sources

**Cutout Data:**
- **CDS (Copernicus):** https://cds.climate.copernicus.eu/
- **Source:** ERA5 reanalysis + SARAH-3 satellite radiation
- **Coverage:** Europe, hourly, 2010-2020

**Zenodo Data:**
- **Repository:** https://zenodo.org/
- **Collections:** PyPSA-Eur community datasets
- **Content:** Power plants, network data, costs, boundaries

---

## Advanced Configuration

To modify data downloads, edit the scripts:

```python
# download_cutout.py
CUTOUT_NAME = "europe-2020-sarah3-era5"
CUTOUT_DIR = Path("data/cutout")
# Modify years, region, resolution here

# download_zenodo_files.py
ZENODO_RECORDS = [
    12345,  # Dataset record ID
    67890,
    # Add more record IDs
]
```

---

## Next Steps

1. **First time:** Run both scripts in sequence
   ```bash
   python download_cutout.py
   python download_zenodo_files.py
   ```

2. **Validate:** Check for completeness
   ```bash
   python ../diagnostics/check_csv.py
   ```

3. **Ready to simulate:** Proceed to runners
   ```bash
   python ../runners/run_baseline_only.bat
   ```

4. **For troubleshooting:** See diagnostics/ folder
