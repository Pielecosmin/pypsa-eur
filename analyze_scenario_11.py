import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import os


# Set GDAL_DATA if missing (fixes warning on Windows)
if 'GDAL_DATA' not in os.environ:
    os.environ['GDAL_DATA'] = r"C:\Users\Administrator\.conda\envs\pypsa-eur\Library\share\gdal"

# Path to the solved network
network_path = "results/romania-adversarial-11-sibiu_regional_crisis/networks/base_s_10_elec_.nc"

if not os.path.exists(network_path):
    print(f"Error: Network file not found at {network_path}")
    print("Simulation might still be running or failed.")
    exit(1)


# Output paths
output_txt = "results/scenario_11_results.txt"
output_img = "results/scenario_11_summary.png"

# Redirect output to both console and file
class Tee:
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()

import sys
# Backup stdout
original_stdout = sys.stdout
# Start logging to file
sys.stdout = Tee(output_txt, "w")

print(f"Loading network from {network_path}...")
n = pypsa.Network(network_path)

print("\n" + "="*50)
print("SCENARIO 11: SIBIU REGIONAL CRISIS ANALYSIS")
print("="*50)

# 1. System Overview
print(f"\nTime range: {n.snapshots[0]} to {n.snapshots[-1]}")
print(f"Objective cost: {n.objective/1e6:.2f} Million EUR")

# 2. Load Shedding (Unmet Demand)
# Check for dummy generators or very high MC generators typically used for load shedding
shedding = n.generators_t.p[n.generators[n.generators.carrier == "load"].index].sum().sum()
if shedding > 0:
    print(f"\nCRITICAL: LOSS OF LOAD DETECTED!")
    print(f"Total Load Shedding: {shedding/1000:.2f} GWh")
else:
    print("\nNo direct load shedding detected (configured carriers).")

# 3. Marginal Prices (Indicator of stress)
try:
    avg_price = n.buses_t.marginal_price.mean().mean()
    max_price = n.buses_t.marginal_price.max().max()
    print(f"\nAverage Marginal Price: {avg_price:.2f} EUR/MWh")
    print(f"Max Marginal Price: {max_price:.2f} EUR/MWh")

    # Identify the most stressed cluster
    stressed_bus_idx = n.buses_t.marginal_price.mean().idxmax()
    print(f"Most stressed region (highest avg price): {stressed_bus_idx}")
    print(f"  Price: {n.buses_t.marginal_price[stressed_bus_idx].mean():.2f} EUR/MWh")
except Exception as e:
    print(f"\nCould not calculate marginal prices: {e}")

# 4. Generation Mix
print("\nGeneration Mix [GWh]:")
gen = n.generators_t.p.sum().groupby(n.generators.carrier).sum() / 1000
print(gen.sort_values(ascending=False).to_markdown())

# 5. Storage Usage
if not n.storage_units_t.state_of_charge.empty:
    print("\nStorage Usage:")
    initial_soc = n.storage_units_t.state_of_charge.iloc[0].sum()
    final_soc = n.storage_units_t.state_of_charge.iloc[-1].sum()
    print(f"Initial SoC: {initial_soc/1000:.2f} GWh")
    print(f"Final SoC:   {final_soc/1000:.2f} GWh")
    print(f"Depletion:   {(initial_soc - final_soc)/1000:.2f} GWh")

# 6. Line Congestion
print("\nTransmission Line Congestion:")
try:
    lines_loading = n.lines_t.p0.abs().mean() / (n.lines.s_nom_opt * n.lines.s_max_pu)
    congested_lines = lines_loading[lines_loading > 0.9]
    print(f"Number of lines > 90% average loading: {len(congested_lines)} / {len(n.lines)}")
    if len(congested_lines) > 0:
        print("Most congested lines:")
        print(congested_lines.sort_values(ascending=False).head(5))
except Exception as e:
    print(f"Could not calculate line loading: {e}")

print("\nAnalysis Complete. Results saved to:", output_txt)

# Restore stdout
# sys.stdout = original_stdout # logic in Tee destructor handles cleanup mostly but explicit is good
# Actually Tee object being garbage collected or script ending will close file. 
# But let's leave it till script end.

# --- PLOTTING ---
print(f"Generating plot to {output_img}...")
fig, ax = plt.subplots(1, 2, figsize=(15, 6))

# Plot 1: Generation Mix
gen.sort_values().plot.barh(ax=ax[0], color='skyblue')
ax[0].set_title("Total Generation by Carrier (GWh)")
ax[0].set_xlabel("GWh")

# Plot 2: Average Marginal Price Timeseries
try:
    n.buses_t.marginal_price.mean(axis=1).plot(ax=ax[1], color='red')
    ax[1].set_title("Average System Marginal Price")
    ax[1].set_ylabel("EUR/MWh")
    ax[1].grid(True, alpha=0.3)
except:
    ax[1].text(0.5, 0.5, "Price data unavailable", ha='center')

plt.tight_layout()
plt.savefig(output_img)
print("Plot saved.")

# --- NETWORK TOPOLOGY MAP ---
output_map = "results/scenario_11_map.png"
print(f"Generating network map to {output_map}...")

def plot_manual_map(n, loading, output_path):
    print("Executing improved manual plotting...")
    # Increase height to accommodate legends at bottom
    fig, ax = plt.subplots(figsize=(12, 14))
    
    # 1. Plot Lines
    for i, line in n.lines.iterrows():
        b0, b1 = line.bus0, line.bus1
        x0, y0 = n.buses.at[b0, 'x'], n.buses.at[b0, 'y']
        x1, y1 = n.buses.at[b1, 'x'], n.buses.at[b1, 'y']
        
        l_val = loading.get(i, 0)
        color = plt.cm.viridis(l_val)
        # Width logic: width = 1 + 3 * (line.s_nom_opt / 5000)
        width = 1 + 3 * (line.s_nom_opt / 5000)
        
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=width, zorder=1, alpha=0.7)

    # 2. Plot Buses (Clusters)
    bus_gen = n.generators_t.p.sum().reindex(n.buses.index, fill_value=0)
    
    # Scatter plot for buses
    ax.scatter(n.buses.x, n.buses.y, 
               s=200 + bus_gen/5, 
               c='orange', edgecolors='black', zorder=3)
    
    # 3. Add Labels with simple de-confliction
    sorted_buses = n.buses.sort_values(by='y')
    for i, bus in sorted_buses.iterrows():
        x, y = bus.x, bus.y
        try:
            idx_num = int(i.split()[-1])
        except:
            idx_num = 0
            
        offset_y = 0.15 
        final_y = y + offset_y if idx_num % 2 == 0 else y - offset_y
            
        ax.text(x, final_y, i, fontsize=10, fontweight='bold', 
                ha='center', va='center', zorder=4,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    ax.set_title("Scenario 11: Network Map (Romania Clusters)", fontsize=16, pad=20)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)

    # --- LEGENDS AT BOTTOM ---
    # Create a separate axis for legends or just use bbox_to_anchor
    
    # Legend 1: Generation Sizes
    sizes = [100, 500, 1000] 
    labels = [f"{s} GWh" for s in sizes]
    leg1_elements = []
    for s, l in zip(sizes, labels):
        leg1_elements.append(plt.Line2D([0], [0], marker='o', color='w', label=l,
                             markerfacecolor='orange', markersize=(200 + s/5)**0.5,
                             markeredgecolor='black'))
    
    # Legend 2: Line Capacities (Widths)
    cap_values = [1000, 3000, 5000]
    cap_labels = [f"{v} MW" for v in cap_values]
    leg2_elements = []
    for v, l in zip(cap_values, cap_labels):
        w = 1 + 3 * (v / 5000)
        leg2_elements.append(plt.Line2D([0], [0], color='gray', linewidth=w, label=l))

    # Place legends below the plot
    leg1 = ax.legend(handles=leg1_elements, title="Generation Capacity", 
                    bbox_to_anchor=(0.25, -0.1), loc='upper center', ncol=3, frameon=True)
    ax.add_artist(leg1)
    
    leg2 = ax.legend(handles=leg2_elements, title="Line Capacity (Width)", 
                    bbox_to_anchor=(0.75, -0.1), loc='upper center', ncol=3, frameon=True)

    # Colorbar at the very bottom
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(0, 1))
    sm.set_array([])
    # Create specific axis for colorbar to place it below legends
    cax = fig.add_axes([0.2, 0.05, 0.6, 0.02])
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_label("Avg. Line Loading (p.u.)", fontsize=12)
    
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    print(f"Improved manual map with bottom legends saved to {output_path}")

try:
    import cartopy.crs as ccrs
    # Calculate line loading for color
    loading = n.lines_t.p0.abs().mean() / (n.lines.s_nom_opt * n.lines.s_max_pu)
    flow = pd.Series(loading, index=n.lines.index)
    
    # Increase height for legends
    fig, ax = plt.subplots(figsize=(10, 14), subplot_kw={"projection": ccrs.PlateCarree()})
    
    # Attempt build-in plot
    collection = n.plot(
        ax=ax,
        bus_sizes=0.01 + 1e-4 * n.generators_t.p.sum().reindex(n.buses.index, fill_value=0),
        bus_colors='orange',
        line_colors=flow,
        line_cmap=plt.cm.viridis,
        line_widths=n.lines.s_nom_opt/2000,
        margin=0.2,
        geomap=True
    )
    
    # Add Legends and Colorbar at bottom (similar logic to manual)
    # Legend 1: Gen
    sizes = [100, 500, 1000] 
    labels = [f"{s} GWh" for s in sizes]
    leg1_elements = [plt.Line2D([0], [0], marker='o', color='w', label=l,
                      markerfacecolor='orange', markersize=10 * (s/1000)**0.5,
                      markeredgecolor='black') for s, l in zip(sizes, labels)]
    
    # Legend 2: Capacity
    cap_values = [1000, 3000, 5000]
    cap_labels = [f"{v} MW" for v in cap_values]
    leg2_elements = [plt.Line2D([0], [0], color='gray', linewidth=v/2000, label=l) 
                      for v, l in zip(cap_values, cap_labels)]

    leg1 = ax.legend(handles=leg1_elements, title="Generation Capacity", 
                    bbox_to_anchor=(0.25, -0.1), loc='upper center', ncol=3, frameon=True)
    ax.add_artist(leg1)
    leg2 = ax.legend(handles=leg2_elements, title="Line Capacity (Width)", 
                    bbox_to_anchor=(0.75, -0.1), loc='upper center', ncol=3, frameon=True)

    cax = fig.add_axes([0.2, 0.05, 0.6, 0.02])
    cbar = plt.colorbar(collection[1], cax=cax, orientation='horizontal')
    cbar.set_label("Avg. Line Loading (p.u.)", fontsize=12)

    # Add labels
    for i, bus in n.buses.iterrows():
        try:
            idx_num = int(i.split()[-1])
        except:
            idx_num = 0
        offset_y = 0.15 
        final_y = bus.y + offset_y if idx_num % 2 == 0 else bus.y - offset_y
        
        ax.text(bus.x, final_y, i, fontsize=8, fontweight='bold', 
                ha='center', va='center', transform=ccrs.PlateCarree(),
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=0.5))
    
    ax.set_title("Scenario 11: Network Map (Cartopy)", fontsize=14)
    plt.savefig(output_map, bbox_inches='tight', dpi=150)
    print("Cartopy map with bottom legends saved.")
except Exception as e:
    print(f"PyPSA/Cartopy plotting failed: {e}")
    # Use improved manual fallback
    loading = n.lines_t.p0.abs().mean() / (n.lines.s_nom_opt * n.lines.s_max_pu)
    plot_manual_map(n, loading, output_map)
