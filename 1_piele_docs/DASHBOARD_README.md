# Dashboard de Vizualizare Scenarii Energie - România

## 🎯 Descriere

Program interactiv în Python (tkinter + matplotlib) pentru analiza și vizualizare scenariilor de bază vs. stres ale sistemului energetic din România. Interfața completă este în limba română.

## 🚀 Cum să rulați

### Prerequisite
Asigurați-vă că ați executat mai întâi scenariile și ați generat rapoartele:

```bash
python run_romania_winter_stress.py
python scripts/report_romania_winter_stress.py \
  --baseline-net results/romania-2019-winter-baseline/networks/base_s_10_elec_.nc \
  --scenario-net results/romania-2020-winter-stress/networks/base_s_10_elec_.nc \
  --country RO \
  --outdir results/romania-2020-winter-stress-comparison
```

### Rulare Dashboard

```bash
python visualize_scenarios_ui.py
```

Fereastra se va deschide cu 6 taburi interactive.

## 📊 Tabulații Disponibile

### 1. 📊 Rezumat (Executive Summary)
- **Metrici principale:** Cost total, ENS, ore de deconectare
- **Comparație bază vs. stres** pe metrice cheie
- **Grafic:** Mix energetic în ambele scenarii

### 2. 💰 Costuri (Cost Analysis)
- **Cost total sistem** pentru bază și stres
- **Delta cost** adiţional datorat stresului
- **Procentaj de creștere** (ex: +128.6%)

### 3. ⚡ Generare (Generation Analysis)
- **Mix energetic** pe tehnologie (hidro, gaze, vânt, etc.)
- **Comparație bară:** bază vs. stres
- **Identifică care surse sunt afectate** de șocuri

### 4. 🔌 Congestie (Congestion Analysis)
- **Încărcare medie** a liniilor de transmisie
- **Comparație bază vs. stres**
- **Identifică blocaje potențiale:**
  - Linia critică dacă >90% →Atenție
  - Linia normală dacă <90% →OK

### 5. 💹 Preț (Price Analysis)
- **Preț marginal local (LMP)** pentru România
- **Metrici:** Medie, P95, Maxim
- **Comparație bază vs. stres**

### 6. 📋 Date Brute (Raw Data)
- **Tabel complet** cu toate datele CSV
- **Selector:** Alegere fișier CSV din dropdown
- **Export:** Salvare fișier CSV la alegere

## 🎮 Butoane Funcționale

| Buton | Funcție |
|-------|---------|
| 🔄 **Reîncarcă Date** | Reîncarcă toate fișierele CSV din disc |
| 💾 **Export CSV** | Salvează datele selectate în fișier nou |
| ❓ **Ajutor** | Afișează instrucțiuni și note |

## 📁 Locații Fișiere Necesare

Dashboard-ul se așteaptă să găsească următoarele fișiere CSV în:
```
results/romania-2020-winter-stress-comparison/
```

Fișierele necesare:
- `system_cost_comparison.csv` - Costuri totale
- `ens_summary.csv` - Energy Not Served (blackout)
- `generation_mix_mwh.csv` - Mix energetic
- `interconnector_flow_congestion.csv` - Congestie linii
- `lmp_summary_ro.csv` - Preț marginal local
- `assumptions_limitations.md` - Limitări

## 📈 Interpretare Grafice

### Green (Bază)
- Scenariu fără șocuri
- Doar condiții climatice normale
- Disponibilitate normală resurse

### Red (Stres)
- Scenariul cu 5 șocuri simultane:
  - Load +12%
  - Hidro -40%
  - Gaze -30%
  - SCADA ramp constraints
  - Import caps

### Delta = Stres - Bază
- Diferența datorată factorilor de stres
- Pozitiv = deteriorare (cost mai mare, ENS mai mare)

## 🔧 Dependențe Python

```
pandas
matplotlib
tkinter (built-in cu Python)
numpy
```

## ⚙️ Configurare Sistem

```bash
# Instalare dependențe (dacă lipsesc)
pip install pandas matplotlib numpy

# Pe Windows cu Conda
conda activate pypsa
python visualize_scenarios_ui.py
```

## 🐛 Troubleshooting

### Eroare: "Director nu găsit"
```
✗ Problema: results/romania-2020-winter-stress-comparison nu există
✓ Soluție: Rulați mai întâi rapoartele cu report_romania_winter_stress.py
```

### Eroare: "No module named 'tkinter'"
```
✗ Windows
✓ Soluție: Reinstalați Python și selectați "tcl/tk and IDLE" în installer

✗ Linux
✓ Soluție: sudo apt-get install python3-tk

✗ macOS
✓ Soluție: Ar trebui inclus; dacă nu: brew install python-tk
```

### Grafice nu se afișează
```
✗ Problema: Matplotlib backend error
✓ Soluție: Asigurați-vă că aveți X11 forwarding dacă e SSH
✓ Soluție: Testați: python -c "import matplotlib; matplotlib.use('Agg')"
```

## 📊 Exemplu Flux Complet

```bash
# 1. Executează scenarii
python run_romania_winter_stress.py

# 2. Generează rapoarte comparative
python scripts/report_romania_winter_stress.py \
  --baseline-net results/romania-2019-winter-baseline/networks/base_s_10_elec_.nc \
  --scenario-net results/romania-2020-winter-stress/networks/base_s_10_elec_.nc \
  --country RO \
  --outdir results/romania-2020-winter-stress-comparison

# 3. Deschide dashboard
python visualize_scenarios_ui.py

# 4. Explorați datele în 6 taburi interactive!
```

## 💡 Sfaturi Utilizare

1. **Start cu Rezumat** - Obțineți perspective generale
2. **Apoi Costuri** - Înțelegeți impactul financiar
3. **Generare & Congestie** - Identificați constrângeri fizice
4. **Preț** - Observați semnale economice
5. **Date Brute** - Verific detaliile specifice

## 📝 Note Importante

- Toate valorile sunt pentru **România (RO)** doar
- Datele acoperă **Dec 1-8, 2020**
- Stresul se aplică **simultan** (5 șocuri in paralel)
- Solver: **HiGHS** cu oprțiuni simplex
- Plafon DNS: **100,000 EUR/MWh**

## 👨‍💻 Contact / Feedback

Pentru sugestii de îmbunătățire ale dashboard-ului:
1. Verificați [PLAN.md](PLAN.md) pentru context proiect
2. Consultați [README3.md](README3.md) pentru structura completă
3. Vezi [results_summary.md](results_summary.md) pentru rezultate

---

**Status:** ✅ Dashboard functional și testat  
**Versiune:** 1.0  
**Data Creare:** 2024  
**Limbă:** Română 🇷🇴 + Engleză
