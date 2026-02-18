
import glob
import yaml
import subprocess
import os
import sys

def run_command(cmd, description):
    print(f"--- {description} ---")
    print(f"Command: {cmd}")
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print(f"Error: Command failed with exit code {ret}")
        return False
    return True

config_files = sorted(glob.glob("config/romania_2020_*.yaml"))

if not config_files:
    print("No config files found!")
    sys.exit(1)

print(f"Found {len(config_files)} scenarios to run.")

for config_file in config_files:
    with open(config_file, 'r') as f:
        cfg = yaml.safe_load(f)
    
    run_name = cfg.get("run", {}).get("name")
    if not run_name:
        print(f"Skipping {config_file}: Could not find run name.")
        continue
    
    # Target file
    # Note: networks/base_s_5_elec_.nc corresponds to the default target for this setup
    target_file = f"results/{run_name}/networks/base_s_5_elec_.nc"
    
    print(f"\n\n==================================================")
    print(f"Processing Scenario: {run_name}")
    print(f"Config: {config_file}")
    print(f"Target: {target_file}")
    print(f"==================================================")
    
    # 1. Unlock
    unlock_cmd = f"conda run -n pypsa snakemake --unlock --configfile {config_file}"
    if not run_command(unlock_cmd, "Unlocking Directory"):
        sys.exit(1)
        
    # 2. Run Simulation
    solve_cmd = f"conda run -n pypsa snakemake -call {target_file} --configfile {config_file}"
    if not run_command(solve_cmd, "Running Simulation"):
        print(f"Simulation failed for {run_name}!")
        sys.exit(1)
        
    print(f"Successfully finished {run_name}")

print("\n\nAll scenarios completed successfully!")
