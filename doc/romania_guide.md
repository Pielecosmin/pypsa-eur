# Romania Simulation Guide (Updated 2020 Scenarios)

## 1. Setup New Data
We have added support for **2020 Scenarios**. Before running them, you must download the 2020 weather data (cutout).

Run one of the following scripts:
```bash
# Downloads both 2013 and 2020 cutouts
python download_cutout.py
```
*Alternatively, `python download_zenodo_files.py` now also includes the 2020 cutout.*

## 2. Available Scenarios (2020)
We have created 5 new configuration files representing different periods in 2020:

| Config File | Period | Season |
|---|---|---|
| `config/romania_2020_winter.yaml` | Jan 1 - Jan 8 | Winter |
| `config/romania_2020_spring.yaml` | Apr 1 - Apr 8 | Spring |
| `config/romania_2020_summer.yaml` | Jul 1 - Jul 8 | Summer |
| `config/romania_2020_autumn.yaml` | Oct 1 - Oct 8 | Autumn |
| `config/romania_2020_december.yaml`| Dec 1 - Dec 8 | Early Winter |

## 3. How to Run a Scenario
To run a specific scenario, use the standard Snakemake command pointing to the desired config file.

**Example: Running the Summer 2020 Scenario**

1. **Unlock directory** (if needed):
   ```bash
   conda run -n pypsa snakemake --unlock --configfile config/romania_2020_summer.yaml
   ```

2. **Run Simulation**:
   ```bash
   conda run -n pypsa snakemake -call results/romania-2020-summer/networks/base_s_5_elec_.nc --configfile config/romania_2020_summer.yaml
   ```

3. **Verify Results**:
   You can manually inspect the results in `results/romania-2020-summer/`.

## 4. Troubleshooting
- **Locked Directory**: If you see "Locked directory", always run the `--unlock` command for the **specific config file** you are using.
- **Missing Data**: Ensure `data/cutout/archive/v0.8/europe-2020-sarah3-era5.nc` exists. If not, run checking/download scripts.