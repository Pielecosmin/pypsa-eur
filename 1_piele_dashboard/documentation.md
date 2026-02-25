# Ghid de Utilizare - Scenario Manager UI și Instrumente de Vizualizare

Acest document explică funcționarea interfeței de gestionare a scenariilor și a instrumentelor de vizualizare pentru modelul PyPSA-Eur România.

## 1. Scenario Manager UI (`scenario_manager_ui.py`)

Acesta este centrul de control principal pentru crearea, configurarea și rularea simulărilor energetice.

### Opțiuni și Configurații

| Opțiune | Explicație |
| :--- | :--- |
| **Clusters** | Reprezintă numărul de regiuni (noduri) în care este împărțită rețeaua electrică. Un număr mai mic (ex. 10) rulează rapid, fiind ideal pentru teste. Un număr mai mare (ex. 50, 100) oferă o precizie geografică mai mare, dar crește timpul de calcul. |
| **Solver** | Motorul matematic care rezolvă optimizarea. <br> - `highs`: Solver open-source modern, foarte rapid (recomandat). <br> - `gurobi`: Solver comercial de înaltă performanță (necesită licență). <br> - `cbc` / `glpk`: Alte opțiuni open-source mai vechi. |
| **Solver Options** | Parametri trimiși către solver. Pentru `highs`, se pot folosi `highs-simplex` (metoda simplex) sau `highs-ipm` (metoda punctului interior). |
| **Run Mode** | `paired` (rulează automat atât scenariul de bază - *baseline* - cât și cel de stres) sau `single` (doar scenariul curent). |
| **Snapshots** | Definește intervalul de timp pentru simulare (ex: o săptămână din decembrie). Formatul este `YYYY-MM-DD`. |
| **Countries** | Lista de țări incluse în model. Implicit este `RO` (România), dar se pot adăuga vecini (ex: `RO,BG,HU,RS`) pentru o analiză mai complexă a importurilor/exporturilor. |

### Parametri de Stres (Stress Factors)
Acști parametri simulează condiții critice:
- **Load Factor**: Multiplicator pentru cererea de energie (ex. `1.12` înseamnă o creștere de 12%).
- **Hydro Factor**: Disponibilitatea energiei hidro (ex. `0.60` înseamnă o reducere la 60% din capacitate).
- **Gas Factor**: Disponibilitatea centralelor pe gaz.
- **SCADA Ramp Constraints**: Limitează viteza cu care generatoarele își pot schimba puterea (ramp rate). Valori mai mici (ex: `0.10`) fac sistemul mai rigid și mai greu de echilibrat.
- **Import Constraints**: Simulează limitări ale importului de energie din țările vecine pe durate specifice (ore).

---

## 2. Instrumente de Vizualizare (Dashboard-uri)

În folderul `1_piele_dashboard/` există două versiuni ale vizualizatorului.

### `visualize_scenarios_ui.py` (Versiunea 1)
- **Ce face**: Este o versiune fixă, configurată să citească automat datele din folderul `results/romania-2020-winter-stress-comparison/`.
- **Scop**: Utilizată pentru o verificare rapidă a scenariului standard de iarnă fără a face setări manuale.

### `visualize_scenarios_ui_v2.py` (Versiunea 2)
- **Ce face**: Este versiunea **dinamică** și îmbunătățită. Permite utilizatorului să:
    - Scaneze automat folderul `results/` pentru orice simulare nouă.
    - Selecteze manual un folder de rezultate folosind un buton de tip "Browse".
    - Redenumească scenariul direct în interfață pentru rapoarte mai clare.
- **Scop**: Recomandată pentru uz general și pentru compararea oricăror scenarii noi create cu Scenario Manager.

**Sunt ambele necesare?**
Nu neapărat. Versiunea **v2** poate face tot ce face v1 și mult mai mult. v1 a fost păstrată pentru stabilitate și pentru utilizatorii care doresc să deschidă direct rezultatul standard fără a selecta foldere, dar pe viitor este recomandată folosirea versiunii **v2**.

---

## 3. Scripturi Python și Rolul Lor

Iată o listă cu principalele scripturi utilizate în acest proiect:

| Script | Rol / De ce este folosit |
| :--- | :--- |
| `scenario_manager_ui.py` | Interfața grafică (GUI) pentru definirea și pornirea simulărilor. |
| `visualize_scenarios_ui_v2.py` | Dashboard-ul principal pentru analiza grafică a rezultatelor. |
| `run_romania_winter_stress.py` | Script de tip "runner" care execută pașii de Snakemake în secvență pentru scenariul de stres. |
| `scripts/report_romania_winter_stress.py` | Scriptul care calculează diferențele dintre scenarii și generează fișierele CSV (ex: `ens_summary.csv`) pe care le citesc vizualizatoarele. |
| `generate_configs.py` | (Anterior UI-ului) Genera automat fișierele YAML de configurare pentru PyPSA. |
| `scenario_manager/run_manager.py` | Logica de fundal care gestionează procesele Snakemake pornite din UI. |

---

## 4. Flux de Lucru Recomandat

1. Deschideți `scenario_manager_ui.py` pentru a configura și rula un scenariu (ex: Iarnă 2026).
2. Așteptați finalizarea execuției (starea "Completed" în UI).
3. Deschideți `visualize_scenarios_ui_v2.py`.
4. Selectați noul folder de rezultate apărut în listă.
5. Analizați graficele pentru Mix Energetic, Costuri, Congestie și Prețuri.
