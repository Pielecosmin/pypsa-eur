import sys
import os
import yaml
import pypsa
import pandas as pd
from types import SimpleNamespace
from pathlib import Path
import traceback

# Add the current directory to path to allow imports from scripts
sys.path.append(os.getcwd())

class DictNamespace(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e
    def __setattr__(self, key, value):
        self[key] = value

SCENARIOS = [
    "romania-2020-december",
    "romania-2020-autumn",
    "romania-2020-spring",
    "romania-2020-summer"
]

def run_make_summary(scenario):
    print(f"--- Running make_summary for {scenario} ---")
    try:
        import scripts.make_summary as make_summary
        
        # Reloading module is not strictly necessary if we just call functions, 
        # but good practice if module has state. make_summary is mostly functional.

        network_file = "base_s_5_elec_.nc"
        network_path = f"results/{scenario}/networks/{network_file}"
        csv_dir = f"results/{scenario}/csvs"
        os.makedirs(csv_dir, exist_ok=True)

        if not os.path.exists(network_path):
            print(f"Network file missing: {network_path}")
            return False

        OUTPUTS = make_summary.OUTPUTS
        
        # Mock snakemake for logging/config if needed, though we use functions directly
        # But we need to configure logging?
        # make_summary.logging.basicConfig(level=make_summary.logging.INFO)

        print(f"Loading network {network_path}...")
        n = pypsa.Network(network_path)
        make_summary.assign_carriers(n)
        make_summary.assign_locations(n)

        pypsa.set_option("params.statistics.nice_names", False)
        pypsa.set_option("params.statistics.drop_zero", False)

        print("Generating CSVs...")
        for output in OUTPUTS:
            print(f"  Generating {output}...")
            func_name = "calculate_" + output
            func = getattr(make_summary, func_name)
            df = func(n)
            df.to_csv(f"{csv_dir}/{output}.csv")
        print(f"make_summary completed for {scenario}.")
        return True

    except Exception as e:
        print(f"Make summary failed for {scenario}: {e}")
        traceback.print_exc()
        return False

def run_plot_summary(scenario, plotting_config):
    print(f"\n--- Running plot_summary for {scenario} ---")
    try:
        import scripts.plot_summary as plot_summary
        
        csv_dir = f"results/{scenario}/csvs"
        graph_dir = f"results/{scenario}/graphs"
        os.makedirs(graph_dir, exist_ok=True)

        # Mock snakemake
        snakemake_plot = SimpleNamespace(
            input=SimpleNamespace(
                costs=f"{csv_dir}/costs.csv",
                energy=f"{csv_dir}/energy.csv",
                balances=f"{csv_dir}/energy_balance.csv",
                eurostat="resources/eurostat", 
                co2="resources/co2.csv"
            ),
            output=SimpleNamespace(
                costs=f"{graph_dir}/costs.png",
                energy=f"{graph_dir}/energy.png",
                balances=f"{graph_dir}/balances-energy.png"
            ),
            params=DictNamespace({
                "plotting": plotting_config,
                "emissions_scope": None,
                "countries": ["RO"],
                "planning_horizons": [2020],
                "RDIR": scenario,
                "sector": {},
                "foresight": "overnight",
                "co2_budget": None
            }),
            config={"foresight": "overnight"}
        )

        # Inject globals
        plot_summary.snakemake = snakemake_plot
        plot_summary.n_header = 1

        print("Plotting costs...")
        plot_summary.plot_costs()
        print(f"Generated {snakemake_plot.output.costs}")

        print("Plotting energy...")
        plot_summary.plot_energy()
        print(f"Generated {snakemake_plot.output.energy}")

        print("Plotting balances...")
        # Adjust for suffix logic
        snakemake_plot.output.balances = f"{graph_dir}/balances-energy.svg"
        plot_summary.plot_balances()
        print(f"Generated balances (SVG)")
        
    except Exception as e:
        print(f"Failed to run plot_summary for {scenario}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Load config once
    with open("config/plotting.default.yaml", "r") as f:
        plotting_config = yaml.safe_load(f)["plotting"]
    
    # Adjust thresholds
    plotting_config["costs_threshold"] = 0.0001
    plotting_config["energy_threshold"] = 0.01

    for scenario in SCENARIOS:
        print(f"\n{'='*40}\nProcessing {scenario}\n{'='*40}")
        if run_make_summary(scenario):
            run_plot_summary(scenario, plotting_config)
    
    print("\nAll scenarios processed.")
