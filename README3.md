# PyPSA-Eur Romania - Scenariu Stres de Iarna 2020
## Documentație Proiect (README3.md)

Acest document descrie extensia PyPSA-Eur pentru simulări complexe de stres a sistemului energetic românesc. Proiectul adaugă funcționalități de analiză a scenariilor de bază vs. stres cu aplicarea de șocuri multiple.

---

## 📁 Structura Proiectului - Fișiere NOI

```
pypsa-eur/
├── config/adversarial/
│   ├── romania_2019_winter_baseline.yaml      # Config: scenariu de bază (fără șocuri)
│   ├── romania_2019_winter_stress.yaml        # Config: scenariu stres (cu toate șocurile)
│   └── [alte scenarii adversariale...]
│
├── scripts/
│   ├── romania_winter_stress.py               # Modul principal de șocuri
│   ├── report_romania_winter_stress.py        # Generator de rapoarte de comparație
│   └── solve_network.py                       # (Modificat) Integrare șocuri în solver
│
├── results/
│   ├── romania-2019-winter-baseline/
│   │   └── networks/base_s_10_elec_.nc       # Rețea reolvată (bază)
│   ├── romania-2020-winter-stress/
│   │   └── networks/base_s_10_elec_.nc       # Rețea rezolvată (stres)
│   └── romania-2020-winter-stress-comparison/
│       ├── system_cost_comparison.csv         # Comparație costuri
│       ├── ens_summary.csv                    # Rezumat energie nelivrată
│       ├── generation_mix_mwh.csv             # Mix de generare
│       ├── daily_net_imports_mwh.csv          # Importuri/exporturi zilnice
│       ├── interconnector_flow_congestion.csv # Congestionare linii
│       ├── lmp_summary_ro.csv                 # Prețuri marginale
│       ├── curtailment_mwh.csv                # Curtare energie regenerabilă
│       ├── fig_01_shedding_timeseries.{png,pdf} # Grafic: deconectări
│       ├── fig_02_daily_net_imports.{png,pdf}   # Grafic: flux importuri
│       ├── fig_03_generation_mix.{png,pdf}      # Grafic: mix generare
│       ├── fig_04_interconnector_loading.{png,pdf} # Grafic: încărcare linii
│       ├── fig_05_ro_price_distribution.{png,pdf}  # Grafic: prețuri
│       └── assumptions_limitations.md         # Documentație asumpții
│
├── run_romania_winter_stress.py               # Orchestrator: rulează bază + stres
├── run_scenario_v2.bat                        # Batch script pentru Windows
├── explore_scenarios.py                       # Script explorare date
├── visualize_scenarios_ui.py                  # (NOU) Dashboard interactiv România
├── README3.md                                 # Acest fișier
└── [fișiere existente...]
```

---

## 🔄 Fluxul de Lucru Complet

### 1. **Configurare Scenarii** (`config/adversarial/*.yaml`)

Două configurații paralele pentru același interval de timp (Dec 1-8, 2020):

#### `romania_2019_winter_baseline.yaml`
- **Run name:** `romania-2019-winter-baseline`
- **Țări:** RO, BG, HU, RS
- **Clustere:** 10 noduri
- **Șocuri:** NICIUN șoc aplicat
- **Utilizare:** Scenariu referință (baseline)

#### `romania_2019_winter_stress.yaml`
- **Run name:** `romania-2020-winter-stress`
- **Țări:** RO, BG, HU, RS (șocuri aplicate doar RO)
- **Clustere:** 10 noduri
- **Șocuri aplicate:**
  - Cerere: +12% pe toată perioada
  - Hidro: 60% disponibilitate
  - Gaz: 70% disponibilitate primele 72h
  - SCADA: Rampă 10%/h (24h), apoi 25%/h (48h)
  - Import cap: 0% (48h), 50% (48h), fără limită (72h)

---

## 🔧 Module Principale

### 2. **Modul Șocuri** (`scripts/romania_winter_stress.py`)

Implementează 3 funcții de bază:

#### `apply_timeseries_shocks(n, snapshots, cfg)`
Aplică șocuri pre-optimizare:
```python
# Incrementează cererea
n.loads_t.p_set *= 1.12

# Reduce disponibilitate hidro
ro_hydro_gens = n.generators[(n.generators.carrier.isin(['ror', 'hydro'])) & 
                              (n.generators.bus.str.contains('RO'))]
ro_hydro_gens.p_max_pu *= 0.60

# Reduce disponibilitate gaz (primele 72 ore)
ga_gens = n.generators[n.generators.carrier.isin(['OCGT', 'CCGT'])]
ga_gens.p_max_pu.iloc[:, :72] *= 0.70
```

#### `add_scada_proxy_constraints(n, snapshots, cfg)`
Adaugă constrângeri de rampă pentru generatoare RO:
- **Ore 1-24:** Rampă ≤ 10% din p_nom/oră
- **Ore 25-72:** Rampă ≤ 25% din p_nom/oră

#### `add_import_cap_constraints(n, snapshots, cfg)`
Limitează importurile la granița RO:
- **Ore 1-48:** Capacitate = 0%
- **Ore 49-96:** Capacitate = 50%
- **Ore 97+:** Fără limită suplimentară

---

### 3. **Generator Rapoarte** (`scripts/report_romania_winter_stress.py`)

Ejecutat post-optimizare. Argumentele CLI:
```bash
python scripts/report_romania_winter_stress.py \
  --baseline-net <cale_bază> \
  --scenario-net <cale_stres> \
  --country RO \
  --outdir <director_ieșire>
```

**Outputs:**
- 7 CSV-uri cu metrici detaliate
- 5 perechi PNG/PDF (figuri)
- 1 document markdown cu asumpții

---

### 4. **Integrare Solver** (`scripts/solve_network.py` - MODIFICAT)

Punerea în aplicare:

**În `prepare_network()`:**
```python
stress_cfg = config.get("stress_test", {})
if stress_cfg.get("enable"):
    apply_timeseries_shocks(n, n.snapshots, stress_cfg)
```

**În `extra_functionality()`:**
```python
if stress_cfg.get("enable"):
    add_scada_proxy_constraints(n, snapshots, stress_cfg)
    add_import_cap_constraints(n, snapshots, stress_cfg)
```

---

## 🚀 Cum să Rulez Simulările

### Pasul 1: Rulare Automată (Recomandată)

```bash
python run_romania_winter_stress.py
```

Aceasta:
1. Deblochează și rezolvă scenariu de bază
2. Deblochează și rezolvă scenariu stres
3. Generează raport de comparație
4. Afișează căi fișiere output

### Pasul 2: Rulare Manuală (Pass-by-Pass)

```bash
# Bază
snakemake --unlock --configfile config/adversarial/romania_2019_winter_baseline.yaml
snakemake solve_elec_networks --configfile config/adversarial/romania_2019_winter_baseline.yaml -c all

# Stres
snakemake --unlock --configfile config/adversarial/romania_2019_winter_stress.yaml
snakemake solve_elec_networks --configfile config/adversarial/romania_2019_winter_stress.yaml -c all

# Raport
python scripts/report_romania_winter_stress.py \
  --baseline-net results/romania-2019-winter-baseline/networks/base_s_10_elec_.nc \
  --scenario-net results/romania-2020-winter-stress/networks/base_s_10_elec_.nc \
  --country RO \
  --outdir results/romania-2020-winter-stress-comparison
```

---

## 📊 Analiză Rezultate

### Fișiere CSV Disponibile

| Fișier | Descriere |
|--------|-----------|
| `system_cost_comparison.csv` | Cost total bază vs. stres (EUR) |
| `ens_summary.csv` | Energie nelivrată, ore deconectare, max MW |
| `generation_mix_mwh.csv` | MWh generat pe tehnologie/caz |
| `daily_net_imports_mwh.csv` | Flux zilnic de importuri/exporturi |
| `interconnector_flow_congestion.csv` | Încărcare linii (%, congestionare) |
| `lmp_summary_ro.csv` | Statistici preț marginal local (EUR/MWh) |
| `curtailment_mwh.csv` | Energie regenerabilă curtată |

### Figuri Disponibile

| Figură | Descriere |
|--------|-----------|
| `fig_01_shedding_timeseries` | Serie temporală deconectări (MW) |
| `fig_02_daily_net_imports` | Importuri/exporturi zilnice (MWh) |
| `fig_03_generation_mix` | Comparație mix generare bază vs. stres |
| `fig_04_interconnector_loading` | Încărcare linii timp |
| `fig_05_ro_price_distribution` | Distribuție prețuri marginale RO |

---

## 🎨 Dashboard Interactiv (`visualize_scenarios_ui.py`)

Program Python complex de vizualizare în limba română:

```bash
python visualize_scenarios_ui.py
```

**Caracteristici:**
- ✅ Interfață taburi: Rezumat, Costuri, Generare, Congestie, Preț
- ✅ Grafice live cu matplotlib
- ✅ Tabele de date interactive
- ✅ Statistici comparative
- ✅ Toate textele în română
- ✅ Export date la CSV

---

## 📈 Rezultate Cheie (Exemplu)

| Metrica | Bază | Stres | Schimbare |
|---------|------|-------|-----------|
| **Cost Total** | €14.94B | €34.15B | +128.6% |
| **ENS (MWh)** | 0 | 26,413 | Crisis! |
| **Max Deconectare** | 0 MW | 2,783 MW | - |
| **Hidro** | 141,876 MWh | 85,125 MWh | -40% |
| **Încope Max Linie** | 28.5% | 32.0% | +3.5pp |

---

## 🔗 Fluxul de Date

```
Config YAML (bază + stres)
        ↓
Snakemake → PyPSA Network Build
        ↓
apply_timeseries_shocks() [Doar stres]
        ↓
Solver HiGHS (Optimizare)
        ↓
add_scada_proxy_constraints() [Doar stres]
add_import_cap_constraints() [Doar stres]
        ↓
Network Solved (.nc file)
        ↓
report_romania_winter_stress.py
        ↓
CSV + Figures + Markdown
        ↓
visualize_scenarios_ui.py [Dashboard]
```

---

## 🛠️ Troubleshooting

### Problema: "MissingInputException: data/cutout/archive/.../europe-2019-era5.nc"
**Soluție:** Configs folosesc 2020, nu 2019. Fișier deja scarcat.

### Problema: "RuleException: build_hydro_profile"
**Soluție:** Interval de timp în snapshot necorespunde cutout. Folosiți 2020-12-01 la 2020-12-08.

### Problema: "No module named 'snakemake'"
**Soluție:** 
```bash
conda activate pypsa-eur
```

### Problema: Dashboard nu se deschide
**Soluție:** Verificați ca fișierele CSV/PNG existe în `results/romania-2020-winter-stress-comparison/`

---

## 📚 Fișiere de Referință

- [PLAN.md](PLAN.md) - Plan detaliat tehnic
- [romania_config_explanation.md](romania_config_explanation.md) - Parametri config
- [README2.md](README2.md) - Workflow scenarii sezonale
- [assumptions_limitations.md](results/romania-2020-winter-stress-comparison/assumptions_limitations.md) - Asumpții stres

---

## ✅ Checklist Rulare

- [ ] Configurații YAML create
- [ ] Module Python create (romania_winter_stress.py, report_*.py)
- [ ] solve_network.py modificat
- [ ] `python run_romania_winter_stress.py` executat cu succes
- [ ] Fișiere output în `results/romania-2020-winter-stress-comparison/`
- [ ] Dashboard `visualize_scenarios_ui.py` funcțional

---

*Actualizat: 18 februarie 2026*
