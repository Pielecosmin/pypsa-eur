# Explicarea fișierului `config/romania.yaml`

Acest fișier este un fișier de configurare pentru **PyPSA-Eur**, personalizat pentru un scenariu specific care implică **România**. Acesta suprascrie setările implicite pentru a defini aria de acoperire, rezoluția și constrângerile simulării sistemului energetic.

## 1. Setări Generale
- **`tutorial: true`**: Indică faptul că aceasta ar putea fi o rulare simplificată sau de tip tutorial, sărindu-se probabil peste unele etape complexe de pre-procesare potrivite pentru rulări la scară largă.
- **`run`**:
  - `name: "romania-test"`: Numele acestei sesiuni de simulare. Rezultatele vor fi probabil stocate într-un director cu acest nume.
  - `disable_progressbar: true`: Dezactivează bara de progres, probabil pentru a menține jurnalele (logs) mai curate.

## 2. Scenariu & Arie de Acoperire
- **`scenario`**:
  - `clusters: [5]`: Rețeaua va fi redusă (clusterizată) la **5 noduri/regiuni**. Aceasta este o granularitate foarte mare, bună pentru teste rapide.
  - `opts: ['']`: Nu se aplică aici opțiuni specifice de optimizare (cum ar fi extinderea liniilor sau limitele de transmisie).
- **`countries: ['RO']`**: Simularea este restrânsă geografic doar la **România**.

## 3. Intervalul de Timp (`snapshots`)
- **Perioada**: `2013-03-01` până la `2013-03-08`.
- **Durata**: **1 săptămână** (7 zile). Acesta este un instantaneu scurt folosit pentru testare, deoarece rulările pentru un an întreg durează mult mai mult.

## 4. Setări Electricitate (`electricity`)
- **Limite CO2**:
  - Activat (`co2limit_enable: true`) cu o limită de `100.e+6` (100 milioane de tone). Aceasta este o constrângere foarte relaxată, permițând efectiv modelului să se concentreze pe minimizarea costurilor fără o decarbonizare strictă pentru acest test.
- **Alegeri Tehnologice** (`extendable_carriers`):
  - **Generatoare**: Solar, Eolian Onshore, Eolian Offshore (AC), Gaz (OCGT, CCGT) și Nuclear sunt permise pentru extindere.
  - **Stocare**: Bateriile sunt permise.
  - **Hidrogen**: Stocarea H2 și conductele de H2 sunt permise.
- **Potențiale Regenerabile**:
  - Utilizează datele **GEM** (Global Energy Monitor) pentru a estima capacitățile existente (`estimate_renewable_capacities: from_gem: true`).

## 5. Date Meteo (`atlite`)
- **Cutout**: `europe-2013-sarah3-era5`.
- Definește limitele spațiale (`x`, `y`) și temporale pentru datele meteo (radiație solară, viteza vântului) utilizate pentru calcularea potențialelor regenerabile.
- **Rezoluție**: Grilă de 0.3 grade.

## 6. Detalii Clusterizare (`clustering`)
- **Excluderi**: `OCGT`, `offwind-ac` și `coal` (cărbune) sunt excluse din procesul de clusterizare, ceea ce înseamnă că capacitățile lor ar putea fi agregate diferit sau păstrate.
- **Rezoluție Temporală**: `resolution_elec: 24h`. Modelul funcționează pe pași **zilnici** (24 de ore) mai degrabă decât orari. Acest lucru reduce semnificativ complexitatea computațională, făcând procesul de rezolvare foarte rapid.

## 7. Rezolvitor / Solver (`solving`)
- **Solver**: `highs`.
- **Opțiuni**: `highs-simplex`.
- HiGHS este un solver de optimizare liniară de înaltă performanță, open-source.

---
**Rezumat pentru Utilizator:**
Această configurație creează o **simulare miniaturală** a sistemului energetic românesc. Agregă țara în doar **5 regiuni**, rulează pentru doar **o săptămână** (Mecrtie 2013) și folosește **pași de timp zilnici**. Permite investiții în regenerabile, gaz, nuclear și hidrogen. Aceasta este probabil destinată depanării, predării sau validării rapide a faptului că configurarea funcționează înainte de a rula simulări costisitoare la scară largă.
