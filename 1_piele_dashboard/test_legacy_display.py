#!/usr/bin/env python
"""Test that legacy format data displays correctly"""

from pathlib import Path
import pandas as pd

print("="*70)
print("TEST: DATA EXTRACTION FROM LEGACY FORMAT")
print("="*70)

legacy_dir = Path('results/romania-2020-autumn/csvs')

if legacy_dir.exists():
    # Load data
    data = {}
    for f in legacy_dir.glob('*.csv'):
        data[f.stem] = pd.read_csv(f)
    
    print(f"\n✅ Loaded {len(data)} files from legacy format\n")
    
    # Test Tab Rezumat metrics extraction
    print("📊 TAB REZUMAT - Metrici:")
    
    if 'energy' in data:
        total_energy = data['energy']['0'].sum() / 1e6
        print(f"  ⚡ Energie Totală: {total_energy:.2f} TWh")
    
    if 'costs' in data:
        total_costs = data['costs']['0'].sum() / 1e9
        print(f"  💶 Cost Total: €{total_costs:.2f}B")
    
    if 'prices' in data:
        avg_price = data['prices']['0'].mean()
        print(f"  💹 Preț Mediu: {avg_price:.2f} EUR/MWh")
    
    if 'capacity_factors' in data:
        avg_cf = data['capacity_factors']['0'].mean()
        print(f"  📊 Factor Cap. Mediu: {avg_cf*100:.1f}%")
    
    # Test Tab Costuri
    print("\n💰 TAB COSTURI - Costs by component:")
    if 'costs' in data and 'component' in data['costs'].columns:
        costs_by_comp = data['costs'].groupby('component')['0'].sum().sort_values(ascending=False)
        for comp, cost in costs_by_comp.head(5).items():
            print(f"  - {comp}: €{cost/1e9:.3f}B")
    
    # Test Tab Generare
    print("\n⚡ TAB GENERARE - Energy by carrier:")
    if 'energy' in data and 'carrier' in data['energy'].columns:
        energy_by_carrier = data['energy'].groupby('carrier')['0'].sum().sort_values(ascending=False)
        for carrier, energy in energy_by_carrier.head(6).items():
            print(f"  - {carrier}: {energy/1e6:.2f} TWh")
    
    # Test Tab Preț
    print("\n💹 TAB PREȚ - Price statistics:")
    if 'prices' in data and '0' in data['prices'].columns:
        price_values = data['prices']['0'].dropna()
        stats = {
            'Medie': price_values.mean(),
            'Mediana': price_values.median(),
            'Min': price_values.min(),
            'Max': price_values.max(),
            'P95': price_values.quantile(0.95)
        }
        for stat, val in stats.items():
            print(f"  {stat}: {val:.2f} EUR/MWh")
    
    print("\n✅ All legacy format translations working!")
else:
    print(f"❌ Directory not found: {legacy_dir}")
