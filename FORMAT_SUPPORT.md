# Suport Format Date - Dashboard v2

## 📊 Două Formate de Date Detectate

Dashboard v2 suportă acum **ambele formate** de date disponibile în proiect:

### ✅ FORMAT NOU (Report)
**Fișier:** `romania-2020-winter-stress-comparison/`

**Fișiere CSV:**
- `system_cost_comparison.csv` - Costuri totale bază vs. scenariu
- `generation_mix_mwh.csv` - Mix energetic
- `ens_summary.csv` - Energy not served (blackout)
- `interconnector_flow_congestion.csv` - Congestie linii
- `lmp_summary_ro.csv` - Preț marginal local
- `curtailment_mwh.csv` - Energie curtată
- `daily_net_imports_mwh.csv` - Importuri zilnice

**Status:** ✅ **SUPORT COMPLET**
- Toate 6 taburi funcționale
- Grafice interactive cu date comparative
- Metrici detaliate (bază vs. scenariu)

---

### 📋 FORMAT LEGACY (Rezultate Native)
**Fișiere:** `romania-2020-summer/csvs`, `romania-2020-autumn/csvs`, etc.

**Fișiere CSV disponibile:**
- `capacities.csv` - Capacități instalate
- `capacity_factors.csv` - Factori de capacitate
- `costs.csv` - Costuri pe componentă
- `curtailment.csv` - Energie curtată
- `energy.csv` - Producție de energie
- `energy_balance.csv` - Bilanț energetic
- `market_values.csv` - Valori de piață
- `metrics.csv` - Metrici aggregate
- `nodal_capacities.csv`, `nodal_costs.csv`, etc. - Date pe nod
- `prices.csv`, `weighted_prices.csv` - Preț

**Status:** ⚠️ **SUPORT PARȚIAL**
- Tab **Rezumat** arată fișierele disponibile
- Taburi **Costuri**, **Generare**, **Congestie**, **Preț** → Mesaj informativ
- Tab **Date Brute** → ✅ Funcțional (exploreaza orice CSV)

---

## 🔄 Cum Lucreaza Detectia

Cand se incarca un scenariu, programul:

1. **Cauta** `system_cost_comparison.csv`
   - ✅ Gasit? → Format NOU, toate taburile active
   - ❌ Nu?: Continua...

2. **Cauta** `costs.csv` + `energy.csv`
   - ✅ Ambele gasite? → Format LEGACY
   - Afiseaza: "⚠️ Format Legacy - Date Disponibile"

3. **Afiseaza status** in barra: `[FORMAT NOU (Report)]` sau `[FORMAT LEGACY (Rezultate native)]`

---

## 🎯 Cazuri de Utilizare

### Cand folositi FORMAT NOU (Winter Stress):
```bash
python visualize_scenarios_ui_v2.py
→ Select: romania-2020-winter-stress-comparison
→ Toate taburile trabalhe perfect
→ Grafice comparare Baza vs. Stres
```

### Cand folositi FORMAT LEGACY (Summer/Autumn/Spring/December):
```bash
python visualize_scenarios_ui_v2.py
→ Select: romania-2020-summer/csvs
→ Tab Rezumat: Arata fisierele disponibile
→ Tab Date Brute: Exploreaza raw CSVs
→ Alte taburi: Mesaj "Necesita format NOU"
```

---

## 💡 Solutii

### Pentru a folosi complet taburile cu date legacy:
Ar fi nevoie de transformation datelor:
- `costs.csv` → `system_cost_comparison.csv`
- `energy.csv` → `generation_mix_mwh.csv`
- etc.

Aceasta ar necesita mapping coloane si agregare pe `case` (baza vs. scenariu).

### Pentru o analiza completa:
**Recomandare:** Rulati raport pe orice scenariu legacy:
```bash
python scripts/report_romania_winter_stress.py \
  --baseline-net results/[scenariul]/networks/base_s_*_elec_.nc \
  --scenario-net results/[scenariul]/networks/base_s_*_elec_.nc \
  --country RO \
  --outdir results/[scenariul]-comparison
```

Aceasta va genera Format NOU cu toate tabelele compatible.

---

## 📊 Tabel Suport

| Tab | Format NOU | Format Legacy |
|-----|----------|---|
| 📊 Rezumat | ✅ Metrici comparative | ⚠️ Lista fișiere |
| 💰 Costuri | ✅ Grafic bază vs. stres | ❌ Mesaj informativ |
| ⚡ Generare | ✅ Mix energetic comparat | ❌ Mesaj informativ |
| 🔌 Congestie | ✅ Linii congestionare | ❌ Mesaj informativ |
| 💹 Preț | ✅ Preț marginal local | ❌ Mesaj informativ |
| 📋 Date Brute | ✅ Toate CSVs + Export | ✅ Toate CSVs + Export |

---

**Versiune:** v2.1  
**Data:** 18 februarie 2026  
**Status:** ✅ Production Ready

Ambele formate sunt acum suportate cu mesaje clare pentru utilizator!
