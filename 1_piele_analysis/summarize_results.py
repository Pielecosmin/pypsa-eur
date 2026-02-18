
import pypsa
import pandas as pd
import os

n = pypsa.Network("results/romania-test/networks/base_s_5_elec_.nc")

print("# PyPSA-Eur Simulation Results: Romania Tutorial")
print(f"\n## System Overview")
# Try to get objective from different attributes depending on version
obj = getattr(n, 'objective', 0)
print(f"- **Total System Cost:** {obj / 1e6:.2f} million EUR/a")
print(f"- **Buses:** {len(n.buses)}")
print(f"- **Generators:** {len(n.generators)}")
print(f"- **Lines:** {len(n.lines)}")

print("\n## Installed Capacities [GW]")
cap = n.generators.groupby("carrier").p_nom_opt.sum() / 1e3
print(cap.to_markdown())

print("\n## Annual Generation [TWh]")
# n.generators_t.p contains the results
gen = n.generators_t.p.sum().groupby(n.generators.carrier).sum() / 1e6
print(gen.to_markdown())

print("\n## Average Marginal Prices [EUR/MWh]")
if not n.buses_t.marginal_price.empty:
    price = n.buses_t.marginal_price.mean().mean()
    print(f"- **Mean Price:** {price:.2f} EUR/MWh")
else:
    print("- **Mean Price:** N/A (Duals not stored)")

# Carrier Generation Share
print("\n## Generation Share [%]")
if gen.sum() > 0:
    share = (gen / gen.sum() * 100).round(2)
    print(share.to_markdown())
else:
    print("No generation recorded.")
