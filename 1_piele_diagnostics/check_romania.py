import pypsa
import os

# Path to the expected output file
network_path = "results/romania-test/networks/base_s_5_elec_.nc"

if not os.path.exists(network_path):
    print(f"Error: Network file not found at {network_path}")
    print("Please make sure you have run the snakemake command successfully.")
    exit(1)

print(f"Loading network from {network_path}...")
n = pypsa.Network(network_path)

print("\n--- Network Summary for Romania Test ---")
print(f"Buses: {len(n.buses)}")
print(f"Lines: {len(n.lines)}")
print(f"Generators: {len(n.generators)}")
print(f"Loads: {len(n.loads)}")

print("\n--- Capacity by Carrier (MW) ---")
print(n.generators.groupby("carrier").p_nom_opt.sum())

print("\n--- Transmission Expansion ---")
print(n.lines[["s_nom", "s_nom_opt"]].head())

print("\nSuccess! You have successfully run and analyzed the Romania test model.")
