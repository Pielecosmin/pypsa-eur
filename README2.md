# PyPSA-Eur Romania Analysis - Project Documentation

This document describes the custom workflow developed for running PyPSA-Eur energy system simulations focused on **Romania**. It covers dataset downloading, scenario configuration, simulation execution, and results analysis.

---

## 📁 Project Structure

```
pypsa-eur/
├── config/
│   ├── romania.yaml                 # Base Romania config (2013 tutorial)
│   ├── romania_2020_winter.yaml     # Winter 2020 scenario
│   ├── romania_2020_spring.yaml     # Spring 2020 scenario
│   ├── romania_2020_summer.yaml     # Summer 2020 scenario
│   ├── romania_2020_autumn.yaml     # Autumn 2020 scenario
│   ├── romania_2020_december.yaml   # December 2020 scenario
│   └── plotting.default.yaml        # Plotting configuration
├── results/
│   ├── romania-test/                # Initial tutorial test run
│   ├── romania-2020-winter/         # Winter scenario results
│   ├── romania-2020-spring/         # Spring scenario results
│   ├── romania-2020-summer/         # Summer scenario results
│   ├── romania-2020-autumn/         # Autumn scenario results
│   └── romania-2020-december/       # December scenario results
├── download_zenodo_files.py         # Download all required datasets
├── download_cutout.py               # Download weather cutouts only
├── generate_configs.py              # Generate seasonal config files
├── run_all_scenarios.py             # Run all seasonal scenarios
├── run_remaining_scenarios.py       # Run specific remaining scenarios
├── run_summary.py                   # Generate CSVs and plots
├── check_romania.py                 # Validate simulation results
├── interpret_results.py             # Analyze December results
├── summarize_results.py             # Summarize tutorial results
├── check_csv.py                     # Validate CSV outputs
└── check_url.py                     # Test Zenodo URL availability
```

---

## 🔧 Prerequisites

- **Conda environment**: `pypsa` with PyPSA-Eur installed
- **Solver**: HiGHS (open-source LP solver)
- **Python packages**: `pypsa`, `pandas`, `matplotlib`, `pyyaml`, `requests`

---

## 📥 Step 1: Download Required Datasets

PyPSA-Eur requires several large datasets from Zenodo that may fail during automatic download (503/504 errors). Use the custom download scripts as a workaround.

### 1.1 Download All Datasets (Recommended)

```bash
python download_zenodo_files.py
```

**Downloads:**
| File | Destination | Size |
|------|-------------|------|
| `europe-2013-sarah3-era5.nc` | `data/cutout/archive/v0.8/` | ~8 GB |
| `europe-2020-sarah3-era5.nc` | `data/cutout/archive/v0.8/` | ~8 GB |
| `LUISA_basemap_020321_50m.tif` | `data/luisa_land_cover/archive/2021-03-02/` | ~1 GB |
| `shipdensity_global.zip` | `data/ship_raster/archive/v5/` | ~500 MB |

### 1.2 Download Weather Cutouts Only

```bash
python download_cutout.py
```

Downloads only the ERA5/SARAH3 weather cutouts for 2013 and 2020.

### 1.3 Check URL Availability

```bash
python check_url.py
```

Tests if Zenodo URLs are accessible before downloading.

---

## ⚙️ Step 2: Configuration

### 2.1 Base Configuration: `config/romania.yaml`

The base configuration for Romania includes:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Country | `RO` | Romania only |
| Clusters | `5` | Network clustered to 5 nodes |
| Time Period | 2013-03-01 to 2013-03-08 | 1 week snapshot |
| Resolution | `24h` | Daily time steps |
| Solver | `highs` | Open-source HiGHS solver |
| CO2 Limit | 100 Mt | Loose constraint for testing |

**Extendable carriers:**
- Generators: Solar, Onshore Wind, Offshore Wind (AC), Gas (OCGT, CCGT), Nuclear
- Storage: Battery, H2 stores
- Links: H2 pipeline

### 2.2 Generate Seasonal Configurations

```bash
python generate_configs.py
```

Creates 5 seasonal configuration files for year 2020:

| Config File | Period | Run Name |
|-------------|--------|----------|
| `romania_2020_winter.yaml` | Jan 1-8, 2020 | romania-2020-winter |
| `romania_2020_spring.yaml` | Apr 1-8, 2020 | romania-2020-spring |
| `romania_2020_summer.yaml` | Jul 1-8, 2020 | romania-2020-summer |
| `romania_2020_autumn.yaml` | Oct 1-8, 2020 | romania-2020-autumn |
| `romania_2020_december.yaml` | Dec 1-8, 2020 | romania-2020-december |

All 2020 scenarios use the `europe-2020-sarah3-era5` weather cutout.

---

## 🚀 Step 3: Run Simulations

### 3.1 Run Single Scenario

```bash
# Unlock the directory (if needed)
conda run -n pypsa snakemake --unlock --configfile config/romania_2020_december.yaml

# Run the simulation
conda run -n pypsa snakemake -call results/romania-2020-december/networks/base_s_5_elec_.nc --configfile config/romania_2020_december.yaml
```

### 3.2 Run All Seasonal Scenarios

```bash
python run_all_scenarios.py
```

Automatically runs all `romania_2020_*.yaml` configurations in sequence.

### 3.3 Run Specific Remaining Scenarios

```bash
python run_remaining_scenarios.py
```

Runs only winter, spring, and summer scenarios (useful if some scenarios already completed).

---

## 📊 Step 4: Analyze Results

### 4.1 Validate Simulation Output

```bash
python check_romania.py
```

Checks if the network file exists and displays:
- Network statistics (buses, lines, generators, loads)
- Capacity by carrier (MW)
- Transmission expansion

### 4.2 Generate Summary CSVs and Plots

```bash
python run_summary.py
```

For each scenario, generates:

**CSV files** (in `results/{scenario}/csvs/`):
- `costs.csv` - System costs breakdown
- `energy.csv` - Energy generation by carrier
- `energy_balance.csv` - Energy balance

**Plot files** (in `results/{scenario}/graphs/`):
- `costs.png` - Cost bar chart
- `energy.png` - Energy bar chart
- `balances-energy.svg` - Energy balance diagram

### 4.3 Interpret December Results

```bash
python interpret_results.py
```

Outputs:
- Network statistics
- Total objective cost (EUR)
- Generation capacities by carrier (GW)
- Network visualization plot (`network_plot.png`)

### 4.4 Summarize Tutorial Results

```bash
python summarize_results.py
```

Prints a markdown-formatted summary of the `romania-test` run including:
- Total system cost
- Installed capacities (GW)
- Annual generation (TWh)
- Average marginal prices (EUR/MWh)
- Generation share (%)

### 4.5 Check CSV Output

```bash
python check_csv.py
```

Displays the first 5 lines of the costs CSV to verify format.

---

## 📂 Results Directory Structure

Each scenario produces the following outputs:

```
results/{scenario}/
├── networks/
│   └── base_s_5_elec_.nc      # Solved network (PyPSA format)
├── csvs/
│   ├── costs.csv
│   ├── energy.csv
│   └── energy_balance.csv
└── graphs/
    ├── costs.png
    ├── energy.png
    └── balances-energy.svg
```

---

## 🐛 Troubleshooting

### Zenodo Download Errors (503/504)

If automatic downloads fail:
1. Run `python check_url.py` to verify URLs
2. Use `python download_zenodo_files.py` for retry logic
3. Or download manually from [Zenodo](https://zenodo.org/) and place in correct folders

### Snakemake Lock Issues

```bash
conda run -n pypsa snakemake --unlock --configfile config/romania.yaml
```

### Missing Network File

If `check_romania.py` fails:
1. Verify the simulation completed without errors
2. Check the target path matches: `results/{run_name}/networks/base_s_5_elec_.nc`

### Incomplete Files Exception

```bash
conda run -n pypsa snakemake --cleanup-metadata {target} --configfile {config}
```

---

## 📚 Additional Documentation

- [romania_config_explanation.md](romania_config_explanation.md) - Detailed explanation of config parameters
- [romania_config_explanation_ro.md](romania_config_explanation_ro.md) - Romanian language explanation
- [results_summary.md](results_summary.md) - Summary of all scenario results

---

## 🏃 Quick Start

```bash
# 1. Download datasets
python download_zenodo_files.py

# 2. Generate seasonal configs
python generate_configs.py

# 3. Run all scenarios
python run_all_scenarios.py

# 4. Generate summaries and plots
python run_summary.py

# 5. Check results
python check_romania.py
```

---

## 📋 Completed Runs

| Scenario | Status | Results Path |
|----------|--------|--------------|
| romania-test | ✅ Complete | `results/romania-test/` |
| romania-2020-winter | ✅ Complete | `results/romania-2020-winter/` |
| romania-2020-spring | ✅ Complete | `results/romania-2020-spring/` |
| romania-2020-summer | ✅ Complete | `results/romania-2020-summer/` |
| romania-2020-autumn | ✅ Complete | `results/romania-2020-autumn/` |
| romania-2020-december | ✅ Complete | `results/romania-2020-december/` |

---

*Last updated: February 2026*

---

## 🇷🇴 Rezultate Scenariul 11: Criza Regională Sibiu

Acest scenariu ("Sibiu Regional Crisis") a simulat o situație extremă constând în:
- **Indisponibilități majore:** Oprirea centralei nucleare Cernavodă, secetă hidrologică severă (20% capacitate), lipsă totală de gaz natural.
- **Restricții de rețea:** Capacitate de transport redusă la 30% și izolare totală față de vecini (fără importuri).
- **Cerere crescută:** Consum majorat cu 20%.

### Rezultate Principale (Săptămâna 1-7 Decembrie 2020)

În ciuda restricțiilor severe, sistemul a reușit să acopere cererea fără deconectări majore de consumatori ("load shedding"), bazându-se pe un mix energetic de urgență:

1.  **Cost Total de Operare:** 25.68 Milioane EUR
2.  **Preț Marginal Mediu:** 17.70 EUR/MWh (Max: 81.16 EUR/MWh în zona RO0 7)
3.  **Mix de Generare:**
    *   ☀️ Solar: ~31 GWh (Sursă principală pe timp de zi)
    *   🟤 Lignit: ~12.5 GWh (Bază de noapte)
    *   💨 Eolian Pe Uscat: ~12.5 GWh
    *   ⚫ Huilă: ~0.4 GWh
    *   ❌ Fără Nuclear, Hidro sau Gaz (indisponibil conform scenariului)

**Concluzie:** Sistemul energetic românesc a demonstrat reziliență în acest scenariu teoretic, reușind să mențină echilibrul prin utilizarea intensivă a capacităților pe cărbune rămase și a producției regenerabile, deși la costuri și emisii ridicate, și cu prețuri marginale locale semnificative.
