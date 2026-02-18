# Activate conda and run snakemake test
$CondaPath = "C:\ProgramData\anaconda3\Scripts\conda.exe"
$EnvName = "pypsa-eur"
$WorkDir = "c:\Users\Administrator\Desktop\newPyPSA\pypsa-eur"

# Initialize conda
& $CondaPath init PowerShell

# Activate environment
conda activate $EnvName

# Change to work directory
Set-Location $WorkDir

# Try dry-run
Write-Host "Running dry-run with baseline config..."
snakemake -n --configfile config/adversarial/romania_2019_winter_baseline.yaml | Select-Object -First 200

Write-Host ""
Write-Host "Checking rule 'all' dependencies..."
snakemake --configfile config/adversarial/romania_2019_winter_baseline.yaml --rulegraph 2>&1 | Head -20
