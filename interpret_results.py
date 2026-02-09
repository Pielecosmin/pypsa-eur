import pypsa
import matplotlib.pyplot as plt
import os

# Path to the solved network file
network_path = r"results/romania-2020-december/networks/base_s_5_elec_.nc"

if not os.path.exists(network_path):
    print(f"Error: File not found at {network_path}")
    exit(1)

print(f"Loading network from {network_path}...")
try:
    n = pypsa.Network(network_path)
    print("Network loaded successfully.")
except Exception as e:
    print(f"Failed to load network: {e}")
    exit(1)

print("\n" + "="*30)
print("       NETWORK STATISTICS       ")
print("="*30)
print(f"Buses:       {len(n.buses)}")
print(f"Lines:       {len(n.lines)}")
print(f"Generators:  {len(n.generators)}")
print(f"Loads:       {len(n.loads)}")
print(f"Storage Units: {len(n.storage_units)}")

print("\n" + "="*30)
print("          TOTAL COST            ")
print("="*30)
print(f"Objective Value: {n.objective:,.2f} EUR")

print("\n" + "="*30)
print("     GENERATION CAPACITIES      ")
print("="*30)
try:
    # Group by carrier and sum p_nom_opt (optimized capacity)
    cap = n.generators.groupby("carrier").p_nom_opt.sum() / 1e3 # GW
    print("Capacity (GW) by carrier:")
    print(cap.sort_values(ascending=False))
except Exception as e:
    print(f"Could not calculate capacities: {e}")

print("\n" + "="*30)
print("        GENERATING PLOT         ")
print("="*30)
try:
    plot_path = "network_plot.png"
    # Basic plot, projecting if possible
    n.plot(title="Romania Network Results", show=False, margin=0.5, geomap=True)
    plt.savefig(plot_path)
    print(f"Plot saved successfully to {os.path.abspath(plot_path)}")
except Exception as e:
    print(f"Plotting failed (this is common in headless environments or if cartopy is missing): {e}")
    print("You can still analyze the data using the text output above.")

print("\n" + "="*30)
print("         NEXT STEPS             ")
print("="*30)
print("1. Open this script in an IDE (VS Code) to experiment.")
print("2. Run 'n.statistics()' in an interactive shell.")
print("3. Check 'scripts/' folder for advanced plotting scripts like 'plot_summary.py'.")
