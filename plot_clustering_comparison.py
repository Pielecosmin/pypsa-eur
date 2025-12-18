
import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pypsa
import os

# Create plots folder if it doesn't exist
os.makedirs("results/romania-test/plots", exist_ok=True)

# Load the unclustered (simplified) network
n = pypsa.Network("resources/romania-test/networks/base_s.nc")

# Standardize attributes to avoid clustering issues with non-standard columns
# (e.g., substation_lv) as shown in the PyPSA documentation
n.lines = n.lines.reindex(columns=n.components["Line"]["defaults"].index[1:])
n.buses = n.buses.reindex(columns=n.components["Bus"]["defaults"].index[1:])

# Define weights for K-means: demand-weighted
loads = (
    n.loads_t.p_set.sum()
    .groupby(n.loads.bus)
    .sum()
    .reindex(index=n.buses.index)
    .fillna(1)
)

# Perform K-means clustering (reduce to 5 nodes)
n_clustered = n.cluster.cluster_spatially_by_kmeans(bus_weightings=loads, n_clusters=5)

# Load Romania country shape for context
states = gpd.read_file("resources/romania-test/country_shapes.geojson")

# Projection for the plot (WGS84)
crs = ccrs.PlateCarree()

# Bounds for Romania
kwargs = {"boundaries": [20, 30, 43, 49]}

fig, axs = plt.subplots(1, 2, subplot_kw={"projection": crs}, figsize=(15, 8))

# Plot 1: Unclustered Network
states.plot(ax=axs[0], edgecolor="black", facecolor="#f0f0f0", alpha=0.5, transform=crs)
n.plot(ax=axs[0], 
       title=f"Original Network ({len(n.buses)} nodes)", 
       bus_size=loads.div(1e6), # Adjusted for visibility
       bus_colors='teal', 
       line_widths=0.5,
       **kwargs)

# Plot 2: Clustered Network (K-means)
states.plot(ax=axs[1], edgecolor="black", facecolor="#f0f0f0", alpha=0.5, transform=crs)
loads_clustered = (
    n_clustered.loads_t.p_set.sum()
    .groupby(n_clustered.loads.bus)
    .sum()
    .reindex(index=n_clustered.buses.index)
)
n_clustered.plot(ax=axs[1], 
                 title=f"Clustered Network (5 nodes)", 
                 bus_size=loads_clustered.div(1e6), 
                 bus_colors='orange', 
                 line_widths=1.5,
                 **kwargs)

plt.suptitle("Romania Spatial Clustering Comparison (K-means)", fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

save_path = "results/romania-test/plots/clustering_comparison.png"
plt.savefig(save_path, dpi=150)
print(f"Plot successfully saved to: {save_path}")
