# Explanation of `config/romania.yaml`

This file is a configuration file for **PyPSA-Eur**, customized for a specific scenario involving **Romania**. It overrides default settings to define the scope, resolution, and constraints of the energy system simulation.

## 1. General Settings
- **`tutorial: true`**: Indicates this might be a simplified or tutorial run, potentially skipping some heavy pre-processing steps suitable for full-scale runs.
- **`run`**:
  - `name: "romania-test"`: The name of this simulation run. Outputs will likely be stored in a directory with this name.
  - `disable_progressbar: true`: Turns off the progress bar, likely to keep logs cleaner.

## 2. Scenario & Scope
- **`scenario`**:
  - `clusters: [5]`: The network will be reduced (clustered) to **5 nodes/regions**. This is very coarse and good for quick testing.
  - `opts: ['']`: No specific optimization options (like line expansion or transmission limits) are applied here.
- **`countries: ['RO']`**: The simulation is restricted geographically to **Romania** only.

## 3. Timeframe (`snapshots`)
- **Period**: `2013-03-01` to `2013-03-08`.
- **Duration**: **1 week** (7 days). This is a short snapshot used for testing, as full-year runs take much longer.

## 4. Electricity Settings (`electricity`)
- **CO2 Limits**:
  - Enabled (`co2limit_enable: true`) with a limit of `100.e+6` (100 million tonnes). This is a very loose constraint effectively allowing the model to focus on cost minimization without strict decarbonization for this test.
- **Technological Choices** (`extendable_carriers`):
  - **Generators**: Solar, Onshore Wind, Offshore Wind (AC), Gas (OCGT, CCGT), and Nuclear are allowed to be expanded.
  - **Storage**: Batteries are allowed.
  - **Hydrogen**: H2 Stores and pipelines are allowed.
- **Renewable Potentials**:
  - Uses **GEM** (Global Energy Monitor) data to estimate existing capacities (`estimate_renewable_capacities: from_gem: true`).

## 5. Weather Data (`atlite`)
- **Cutout**: `europe-2013-sarah3-era5`.
- Defines the spatial (`x`, `y`) and temporal bounds for weather data (solar radiation, wind speed) used to calculate renewable potentials.
- **Resolution**: 0.3 degrees grid.

## 6. Clustering Details (`clustering`)
- **Exclusions**: `OCGT`, `offwind-ac`, and `coal` are excluded from the clustering process, meaning their capacities might be aggregated differently or preserved.
- **Temporal Resolution**: `resolution_elec: 24h`. The model operates on **daily** steps (24 hours) rather than hourly. This significantly reduces computational complexity, making the solving process very fast.

## 7. Solver (`solving`)
- **Solver**: `highs`.
- **Options**: `highs-simplex`.
- HiGHS is an open-source high-performance linear optimization solver.

---
**Summary for User:**
This config creates a **miniature simulation** of the Romanian power system. It aggregates the country into just **5 regions**, runs for only **one week** (March 2013), and uses **daily time steps**. It allows investment in renewables, gas, nuclear, and hydrogen. This is likely intended for debugging, teaching, or quickly validating that the setup works before running expensive full-scale simulations.
