@echo off
setlocal enabledelayedexpansion

REM Activate conda
call "C:\ProgramData\anaconda3\Scripts\activate.bat" pypsa-eur

cd /d "c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur"

echo Running Romania Winter 2020 Baseline and Stress Scenarios...

echo.
echo --- Unlock baseline workflow ---
snakemake --unlock --configfile config/adversarial/romania_2019_winter_baseline.yaml
if errorlevel 1 (
    echo Error unlocking baseline
    goto error
)

echo.
echo --- Solve baseline scenario (default target) ---
snakemake solve_elec_networks --configfile config/adversarial/romania_2019_winter_baseline.yaml -c all --resources mem_mb=32000 runtime=360
if errorlevel 1 (
    echo Error solving baseline
    goto error
)

echo.
echo --- Unlock stress workflow ---
snakemake --unlock --configfile config/adversarial/romania_2019_winter_stress.yaml
if errorlevel 1 (
    echo Error unlocking stress
    goto error
)

echo.
echo --- Solve stress scenario (default target) ---
snakemake solve_elec_networks --configfile config/adversarial/romania_2019_winter_stress.yaml -c all --resources mem_mb=32000 runtime=360
if errorlevel 1 (
    echo Error solving stress
    goto error
)

echo.
echo Basic scenarios completed. Networks should be generated.
echo Checking generated files...

dir results\romania-2020-winter-baseline\networks\ 2>nul
dir results\romania-2020-winter-stress\networks\ 2>nul

echo.
echo Scenarios completed!
goto done

:error
echo.
echo Run failed with error!
exit /b 1

:done
exit /b 0
