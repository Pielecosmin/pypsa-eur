
import yaml
import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"--- {description} ---")
    print(f"Command: {cmd}")
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print(f"Error: Command failed with exit code {ret}")
        return False
    return True

# Specific configs to run
config_files = [
    "config/romania_2020_winter.yaml",
    "config/romania_2020_spring.yaml",
    "config/romania_2020_summer.yaml"
]

print(f"Running {len(config_files)} remaining scenarios...")

for config_file in config_files:
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        continue

    with open(config_file, 'r') as f:
        cfg = yaml.safe_load(f)
    
    run_name = cfg.get("run", {}).get("name")
    target_file = f"results/{run_name}/networks/base_s_5_elec_.nc"
    
    print(f"\n\n==================================================")
    print(f"Processing Scenario: {run_name}")
    print(f"==================================================")
    
    # 1. Unlock
    unlock_cmd = f"conda run -n pypsa snakemake --unlock --configfile {config_file}"
    if not run_command(unlock_cmd, "Unlocking Directory"):
        sys.exit(1)
        
    # 2. Run Simulation
    solve_cmd = f"conda run -n pypsa snakemake -c 1 {target_file} --configfile {config_file}"
    if not run_command(solve_cmd, "Running Simulation"):
        print(f"Simulation failed for {run_name}!")
        sys.exit(1)
        
    print(f"Successfully finished {run_name}")

print("\n\nRemaining scenarios completed successfully!")
