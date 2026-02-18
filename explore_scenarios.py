#!/usr/bin/env python
"""
Explore Romania scenario networks
"""
import pypsa
import pandas as pd

# Load both networks
baseline = pypsa.Network('results/romania-2019-winter-baseline/networks/base_s_10_elec_.nc')
stress = pypsa.Network('results/romania-2020-winter-stress/networks/base_s_10_elec_.nc')

print("\n" + "="*70)
print("ROMANIA WINTER SCENARIO COMPARISON")
print("="*70)

# Summary
print("\n1. COSTS:")
print(f"   Baseline: €{baseline.objective:.2e}")
print(f"   Stress:   €{stress.objective:.2e}")
print(f"   Delta:    €{stress.objective - baseline.objective:.2e} (+{((stress.objective/baseline.objective - 1)*100):.1f}%)")

# Generation by carrier
print("\n2. GENERATION BY CARRIER (Total MWh):")
print("\nBaseline:")
for carrier in baseline.generators.carrier.unique():
    gen = baseline.generators[baseline.generators.carrier == carrier]
    total = gen.p_nom.sum() if len(gen) > 0 else 0
    print(f"  {carrier:12s}: {total:8.1f} MW")

print("\nStress:")
for carrier in stress.generators.carrier.unique():
    gen = stress.generators[stress.generators.carrier == carrier]
    total = gen.p_nom.sum() if len(gen) > 0 else 0
    print(f"  {carrier:12s}: {total:8.1f} MW")

# Load info
print("\n3. LOADS:")
print(f"   Baseline total: {baseline.loads.p_set.sum().sum():.1f} MWh")
print(f"   Stress total:   {stress.loads.p_set.sum().sum():.1f} MWh")
print(f"   Delta:          {((stress.loads.p_set.sum().sum() / baseline.loads.p_set.sum().sum() - 1)*100):.1f}%")

# Line congestion
print("\n4. LINE LOADING (mean % of capacity):")
baseline_loading = (baseline.lines_t.p0.abs() / baseline.lines.s_nom).mean() * 100
stress_loading = (stress.lines_t.p0.abs() / stress.lines.s_nom).mean() * 100
print(f"   Baseline: {baseline_loading.mean():.1f}%")
print(f"   Stress:   {stress_loading.mean():.1f}%")

print("\n" + "="*70)
print("\nTo explore further:")
print("  baseline.generators")
print("  baseline.loads_t.p_set")
print("  baseline.lines_t.p0")
print("  baseline.generators_t.p")
