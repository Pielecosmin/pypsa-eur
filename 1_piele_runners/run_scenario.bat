@echo off
setlocal enabledelayedexpansion

echo Running Romania Winter 2019 Baseline Scenario...
call conda.bat activate pypsa-eur

echo --- Unlock baseline workflow ---
call snakemake --unlock --configfile config/adversarial/romania_2019_winter_baseline.yaml
if errorlevel 1 goto error

echo --- Solve baseline scenario ---
call snakemake -c all results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc --configfile config/adversarial/romania_2019_winter_baseline.yaml
if errorlevel 1 goto error

echo --- Unlock stress workflow ---
call snakemake --unlock --configfile config/adversarial/romania_2019_winter_stress.yaml
if errorlevel 1 goto error

echo --- Solve stress scenario ---
call snakemake -c all results/romania-2020-winter-stress/networks/base_s_10_elec_.nc --configfile config/adversarial/romania_2019_winter_stress.yaml
if errorlevel 1 goto error

echo --- Generate comparison report ---
python scripts/report_romania_winter_stress.py --baseline-net results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc --scenario-net results/romania-2020-winter-stress/networks/base_s_10_elec_.nc --country RO --outdir results/romania-2020-winter-stress-comparison
if errorlevel 1 goto error

echo Completed successfully.
echo - Baseline network: results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc
echo - Stress network:   results/romania-2020-winter-stress/networks/base_s_10_elec_.nc
echo - Report folder:    results/romania-2020-winter-stress-comparison
goto done

:error
echo Run failed with error code %errorlevel%
exit /b %errorlevel%

:done
