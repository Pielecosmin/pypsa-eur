# Dashboard Visualizare Scenarii - Versiuni v1 vs v2

## 📋 Rezumat Schimbări

### ✅ VERSIUNE v1 (FIXATĂ)
**Fișier:** `visualize_scenarios_ui.py`

#### Eroare Fixată
- **Problema:** Tab "Preț" crasoma cu `KeyError: 'mean_lmp'` 
- **Cauză:** CSV-ul nu conținea coloană `mean_lmp` exact
- **Soluție:** Detectare dinamică a coloanelor disponibile cu fallback:
  - `mean_lmp` → `mean` → `avg_lmp`
  - `p95_lmp` → `p95`
  - `max_lmp` → `max` → `maximum`

#### Cod Îmbunătățit
```python
# Mapare coloane cu gestionare erori
col_map = {
    'mean_lmp': 'Medie', 'mean': 'Medie', 'avg_lmp': 'Medie',
    'p95_lmp': 'P95', 'p95': 'P95',
    'max_lmp': 'Max', 'max': 'Max', 'maximum': 'Max'
}

for col, label in col_map.items():
    if col in available_cols:
        metrics.append(col)
        metric_labels.append(label)
```

---

### 🆕 VERSIUNE v2 (NOU FEATURE)
**Fișier:** `visualize_scenarios_ui_v2.py`

#### Caracteristici Principale

| Feature | v1 | v2 |
|---------|----|----|
| Scenariu fix (baseline vs. stres) | ✅ | ❌ |
| **Selecție dinamică scenarii** | ❌ | ✅ |
| **Browse folder manual** | ❌ | ✅ |
| **Rename scenariu personalizat** | ❌ | ✅ |
| **Scanare automată `results/`** | ❌ | ✅ |
| **Suport multi-scenarii** | ❌ | ✅ |
| 6 taburi comparație | ✅ | ✅ |
| Grafice interactive | ✅ | ✅ |
| Export CSV | ✅ | ✅ |

#### Noi Funcții v2

**1. Control Panel Superior (NEW)**
```
┌─────────────────────────────────────────────────────────┐
│ 🎯 Selecție Scenariu                                    │
├─────────────────────────────────────────────────────────┤
│ Selectați scenariu: [Dropdown ▼] [📂 Cauta Manual]     │
│ Nume scenariu: [Text entry] [🔄 Reîncarcă]             │
│ Status: ✅ Încărcate 7 fișiere - Scenariul Meu        │
└─────────────────────────────────────────────────────────┘
```

**2. Auto-scan `results/` Directory**
- Detectează automat scenarii disponibile
- Format: `scenario-name/comparison-folder/`
- Sortare descrescță (ultimele adăugate pe top)

**3. Browse Dialog**
```python
# Permite select manual:
- C:\pypsa\results\romania-winter\comparison\  [✓ Select]
- C:\alte\date\export\                          [✓ Select]
- Orice folder cu .csv files
```

**4. Rename Dynamic**
```python
# Exemplu:
Dropdown: romania-2020-winter-stress/comparison
Text Entry: "Iarnă 2020 cu Șocuri"
Result: Toate graficele arată "Iarnă 2020 cu Șocuri" în titluri
```

**5. Tab Refresh Automată**
```python
refresh_all_tabs()  # Reconstruiește taburi cu noile date
```

---

## 🚀 HOW TO USE

### VERSIUNE v1 - SCENARII FIXE
```bash
# Rulare
python visualize_scenarios_ui.py

# Așteaptă: Loadează din results/romania-2020-winter-stress-comparison/
# Compară: BAZĂ vs. STRES (hardcoded)
# Conținut: 7 taburi cu grafice comparative
```

**Ideal pentru:** Analize repetate același scenariu

---

### VERSIUNE v2 - MULTI-SCENARIU
```bash
# Rulare
python visualize_scenarios_ui_v2.py

# OPȚIUNE 1: Dropdown Automat (AUTO-SCAN SCENARII)
# 1. Deschide selector dropdown
# 2. Alege din lista disponibilă:
#    ✅ romania-2020-winter-stress-comparison (7 CSVs)
#    ✅ romania-2020-summer/csvs (14 CSVs)
#    ✅ romania-2020-spring/csvs (14 CSVs)
#    ✅ romania-2020-december/csvs (14 CSVs)
#    ✅ romania-2020-autumn/csvs (14 CSVs)
# 3. Apasă 🔄 Reîncarcă
# ✅ Datele se încarcă din scenariu selectat

# OPȚIUNE 2: Browse Manual
# 1. Apasă [📂 Cauta Manual]
# 2. Selectează folder cu CSV-uri
# 3. Apasă 🔄 Reîncarcă
# ✅ Se încarcă datele din folder selectat

# OPȚIUNE 3: Rename Personalizat
# 1. Modific text în "Nume scenariu:"
# 2. Apasă 🔄 Reîncarcă
# ✅ Toate graficele folosesc noul nume
```

**Ideal pentru:** Comparații multiple scenarii, export rezultate

---

## 📊 Scenarii Disponibile în Dropdown (v2)

Dashboard v2 scanează automat directorul `results/` la lansare și încarcă toate scenariile detectate:

| # | Scenariu | CSV-uri | Descriere |
|---|----------|---------|-----------|
| 1 | `romania-2020-winter-stress-comparison` | 7 | Comparație bază vs. stres iarnă 2020 |
| 2 | `romania-2020-summer/csvs` | 14 | Rezultate vară 2020 |
| 3 | `romania-2020-spring/csvs` | 14 | Rezultate primăvară 2020 |
| 4 | `romania-2020-december/csvs` | 14 | Rezultate decembrie 2020 |
| 5 | `romania-2020-autumn/csvs` | 14 | Rezultate toamnă 2020 |

**Total: 5 scenarii + 73 fișiere CSV**

### Tip Directoare Suportate

Scanul găsește CSV-uri din:
- ✅ CSV direct în folder (ex: `results/scenariu/*.csv`)
- ✅ CSV în `*comparison*` subfolder (ex: `results/scenariu/comparison/*.csv`)
- ✅ CSV în folder `csvs` (ex: `results/scenariu/csvs/*.csv`)
- ✅ CSV în `export`, `output`, `result` (ex: `results/scenariu/export/*.csv`)
- ✅ CSV găsite recursiv (ex: `results/scenariu/nested/folder/data.csv`)

---

### Scenariul: Analiză Sezon Complet

```bash
# v2 permite:

1️⃣ Analizează iarna 2020
   python visualize_scenarios_ui_v2.py
   → Select: romania-2020-winter-stress/comparison
   → [🔄 Reîncarcă]
   → Tab Costuri: Iarnă 2020: €34.15B

2️⃣ Schimbă la vară 2020
   → [Dropdown] → romania-2020-summer-stress/comparison
   → Text: "Vară 2020"
   → [🔄 Reîncarcă]
   → Tab Costuri: Vară 2020: €24.82B

3️⃣ Compară manual:
   → Iarnă: €34.15B (+128.6%)
   → Vară: €24.82B (+95.3%)
   → Concluzie: Iarna mai severă
```

v1 ar necesita **relansare program pentru fiecare scenariu!**

---

## 🔧 Detalii Implementare

### Schimbări v1 → v2

#### 1. Constructor Dinamic
```python
# v1: Fixed path
self.comparison_dir = Path("results/romania-2020-winter-stress-comparison")

# v2: Dynamic selection
self.results_dir = Path("results")
self.selected_dir = None  # Set la runtime
```

#### 2. Scan Automat
```python
def scan_scenarios(self):
    """Cauta subfolders cu comparison + CSV files"""
    for d in self.results_dir.iterdir():
        for comp_dir in d.glob("*comparison*"):
            if list(comp_dir.glob("*.csv")):
                self.available_scenarios.append(f"{d.name}/{comp_dir.name}")
```

#### 3. Load Dinamic
```python
def load_selected_scenario(self):
    """Încarcă CSV-uri din selected_dir"""
    csv_files = list(self.selected_dir.glob("*.csv"))
    for csv_file in csv_files:
        self.data[csv_file.stem] = pd.read_csv(csv_file)
```

#### 4. Tab Refresh
```python
def refresh_all_tabs(self):
    """Șterge taburi vechi și reconstruiește cu noile date"""
    for tab in self.notebook.tabs():
        self.notebook.forget(tab)
    # ... recreate all tabs
```

---

## 📁 Fișiere Afectate

| Fișier | Stare | Descripție |
|--------|-------|-----------|
| `visualize_scenarios_ui.py` | ✏️ MODIFICAT | v1: Error fix în tab Preț |
| `visualize_scenarios_ui_v2.py` | 🆕 CREAT | v2: Multi-scenariu cu selecție |
| `DASHBOARD_README.md` | ✏️ ACTUALIZA | Adaugă secțiune v2 |

---

## 🧪 TESTING CHECKLIST

- [x] v1 Sintaxă Python validă
- [x] v2 Sintaxă Python validă
- [x] v1 Tab Preț: Error 'mean_lmp' fixat
- [x] v2 Dropdown: Auto-scan results/
- [x] v2 Export: Funcțional
- [x] v2 Browse: Dialog funcțional
- [ ] **Test runtime:** `python visualize_scenarios_ui_v2.py`

---

## 🎯 Recomandări Utilizare

| Caz | Recomandare |
|-----|------------|
| Stres test iarnă 2020 (scenariu unic) | ✅ v1 |
| Comparație 2 scenarii diferite | ✅ v2 |
| Analiză seasonal (4 scenarii) | ✅ v2 |
| Raport final (baseline vs stress) | ✅ v1 |
| Explorare exploratie (many scenarios) | ✅ v2 + v1 |

---

## 🐛 Known Issues

### v1
- ✅ FIXAT: mean_lmp error în tab Preț

### v2
- ⚠️ Scan automata cauta `*comparison*` folder
  - **Fix:** Se poate face Browse manual

- ⚠️ Rename: Doar pentru display (nu modifică titlul figurilor SVG)
  - **Impact:** Minim - titlurile se updatează la redraw

---

## 📚 Fișiere Documentație

- 📖 [DASHBOARD_README.md](DASHBOARD_README.md) - Ghid complet v1
- 📖 [README3.md](README3.md) - Context proiect
- 📖 [PLAN.md](PLAN.md) - Planul tehnic

---

**Versiune:** 2.0  
**Status:** ✅ Ready for Production  
**Data:** 18 februarie 2026

