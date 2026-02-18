@echo off
setlocal enabledelayedexpansion

REM Activate conda
call "C:\ProgramData\anaconda3\Scripts\activate.bat" pypsa-eur

cd /d "c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur"

echo.
echo --- Solving baseline scenario only ---
snakemake solve_elec_networks --configfile config/adversarial/romania_2019_winter_baseline.yaml -c all --resources mem_mb=32000 runtime=360

if errorlevel 1 (
    echo Error solving baseline
    exit /b 1
)

echo.
echo Baseline scenario completed.
dir results\romania-2020-winter-baseline\networks\ 2>nul

exit /b 0
