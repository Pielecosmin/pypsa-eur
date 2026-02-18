#!/usr/bin/env python
"""
PyPSA-Eur Romania - Dashboard de Vizualizare Scenarii
Program interactiv pentru analiza scenariilor de bază vs. stres
Toate textele în limba română
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from pathlib import Path
import numpy as np

class DashboardRomania:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Scenarii Energy - PyPSA-Eur România")
        self.root.geometry("1400x900")
        
        # Setări default
        self.comparison_dir = Path("results/romania-2020-winter-stress-comparison")
        self.data = {}
        self.load_all_data()
        
        # Creare interfață cu taburi
        self.create_ui()
        
    def load_all_data(self):
        """Încarcă toate datele CSV disponibile"""
        try:
            if self.comparison_dir.exists():
                csv_files = list(self.comparison_dir.glob("*.csv"))
                for csv_file in csv_files:
                    self.data[csv_file.stem] = pd.read_csv(csv_file)
                messagebox.showinfo("Succes", f"Încărcate {len(csv_files)} fișiere CSV")
            else:
                messagebox.showwarning("Atenție", 
                    f"Director nu găsit: {self.comparison_dir}\n\n"
                    "Rulați mai întâi:\npython scripts/report_romania_winter_stress.py")
        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la încărcare date:\n{e}")
    
    def create_ui(self):
        """Creează interfața cu taburi"""
        # Bară de instrumente
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 Reîncarcă Date", command=self.load_all_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Export CSV", command=self.export_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❓ Ajutor", command=self.show_help).pack(side=tk.LEFT, padx=2)
        
        # Taburi principale
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Construiește taburi
        self.create_tab_resumat()
        self.create_tab_costuri()
        self.create_tab_generare()
        self.create_tab_congestie()
        self.create_tab_pret()
        self.create_tab_date_brute()
        
    def create_tab_resumat(self):
        """Tab 1: Rezumat Executiv"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Rezumat")
        
        # Painel stânga - Statistici
        left = ttk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(left, text="METRICI PRINCIPALE", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        metrics_frame = ttk.LabelFrame(left, text="Comparație Bază vs. Stres", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        try:
            cost_data = self.data.get('system_cost_comparison')
            if cost_data is not None:
                baseline_cost = cost_data.iloc[0]['baseline_total_system_cost_eur']
                stress_cost = cost_data.iloc[0]['scenario_total_system_cost_eur']
                delta = stress_cost - baseline_cost
                delta_pct = (delta / baseline_cost) * 100
                
                metrics = [
                    ("💶 Cost Bază", f"€{baseline_cost/1e9:.2f}B"),
                    ("💶 Cost Stres", f"€{stress_cost/1e9:.2f}B"),
                    ("📈 Delta Cost", f"€{delta/1e9:.2f}B (+{delta_pct:.1f}%)"),
                ]
                
                for label, value in metrics:
                    row = ttk.Frame(metrics_frame)
                    row.pack(fill=tk.X, pady=5)
                    ttk.Label(row, text=label, width=20).pack(side=tk.LEFT)
                    ttk.Label(row, text=value, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
            
            ens_data = self.data.get('ens_summary')
            if ens_data is not None:
                ens_values = {
                    row['case']: {
                        'ens_mwh': row['ens_mwh'],
                        'hours': row['hours_with_shedding'],
                        'max_mw': row['max_shedding_mw']
                    }
                    for _, row in ens_data.iterrows()
                }
                
                ttk.Separator(metrics_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
                
                ens_baseline = ens_values.get('baseline', {})
                ens_scenario = ens_values.get('scenario', {})
                
                metrics2 = [
                    ("⚡ ENS Bază", f"{ens_baseline.get('ens_mwh', 0):.0f} MWh"),
                    ("⚡ ENS Stres", f"{ens_scenario.get('ens_mwh', 0):.0f} MWh"),
                    ("⏱️ Ore Deconectare", f"{ens_scenario.get('hours', 0):.0f}"),
                    ("📊 Max Deconectare", f"{ens_scenario.get('max_mw', 0):.0f} MW"),
                ]
                
                for label, value in metrics2:
                    row = ttk.Frame(metrics_frame)
                    row.pack(fill=tk.X, pady=5)
                    ttk.Label(row, text=label, width=20).pack(side=tk.LEFT)
                    ttk.Label(row, text=value, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        
        except Exception as e:
            ttk.Label(metrics_frame, text=f"Eroare: {e}").pack()
        
        # Painel dreapta - Grafic generare
        right = ttk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(right, text="MIX DE GENERARE (Bază vs. Stres)", font=("Arial", 12, "bold")).pack()
        
        try:
            gen_data = self.data.get('generation_mix_mwh')
            if gen_data is not None:
                fig = Figure(figsize=(6, 4), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline = gen_data[gen_data['case'] == 'baseline']
                scenario = gen_data[gen_data['case'] == 'scenario']
                
                x = np.arange(len(baseline))
                width = 0.35
                
                ax.bar(x - width/2, baseline['generation_mwh'], width, label='Bază', alpha=0.8)
                ax.bar(x + width/2, scenario['generation_mwh'], width, label='Stres', alpha=0.8)
                
                ax.set_xlabel('Tehnologie')
                ax.set_ylabel('Generare (MWh)')
                ax.set_title('Comparație Mix Generare')
                ax.set_xticks(x)
                ax.set_xticklabels(baseline['carrier'], rotation=45, ha='right', fontsize=8)
                ax.legend()
                ax.grid(True, alpha=0.3)
                fig.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, master=right)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(right, text=f"Eroare grafic: {e}").pack()
    
    def create_tab_costuri(self):
        """Tab 2: Analiza Costuri"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💰 Costuri")
        
        try:
            cost_data = self.data.get('system_cost_comparison')
            if cost_data is not None:
                baseline_cost = cost_data.iloc[0]['baseline_total_system_cost_eur']
                stress_cost = cost_data.iloc[0]['scenario_total_system_cost_eur']
                
                fig = Figure(figsize=(10, 6), dpi=80)
                
                # Suplot 1: Cost comparison
                ax1 = fig.add_subplot(121)
                cases = ['Bază', 'Stres']
                costs = [baseline_cost/1e9, stress_cost/1e9]
                colors = ['#2ecc71', '#e74c3c']
                bars = ax1.bar(cases, costs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
                ax1.set_ylabel('Cost (Miliarde EUR)')
                ax1.set_title('Cost Total Sistem')
                ax1.grid(True, alpha=0.3, axis='y')
                
                # Adaugă valori pe bare
                for bar, cost in zip(bars, costs):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'€{cost:.2f}B', ha='center', va='bottom', fontsize=11, fontweight='bold')
                
                # Suplot 2: Delta
                ax2 = fig.add_subplot(122)
                delta = stress_cost - baseline_cost
                delta_pct = (delta / baseline_cost) * 100
                ax2.bar(['Cost Adiţional'], [delta/1e9], color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=2)
                ax2.set_ylabel('Cost Adiţional (Miliarde EUR)')
                ax2.set_title(f'Cost Stres vs. Bază\n+{delta_pct:.1f}%')
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.text(0, delta/1e9, f'€{delta/1e9:.2f}B', ha='center', va='bottom', fontsize=11, fontweight='bold')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}").pack()
    
    def create_tab_generare(self):
        """Tab 3: Analiza Generare"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚡ Generare")
        
        try:
            gen_data = self.data.get('generation_mix_mwh')
            if gen_data is not None:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline = gen_data[gen_data['case'] == 'baseline'].set_index('carrier')
                scenario = gen_data[gen_data['case'] == 'scenario'].set_index('carrier')
                
                x = np.arange(len(baseline))
                width = 0.35
                
                ax.bar(x - width/2, baseline['generation_mwh'], width, label='Bază', alpha=0.8, color='#3498db')
                ax.bar(x + width/2, scenario['generation_mwh'], width, label='Stres', alpha=0.8, color='#e74c3c')
                
                ax.set_xlabel('Technologie', fontsize=12)
                ax.set_ylabel('Generare (MWh)', fontsize=12)
                ax.set_title('Mix Energetic: Bază vs. Stres', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(baseline.index, rotation=45, ha='right')
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}").pack()
    
    def create_tab_congestie(self):
        """Tab 4: Congestie Linii"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔌 Congestie")
        
        try:
            cong_data = self.data.get('interconnector_flow_congestion')
            if cong_data is not None:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline_lines = cong_data[cong_data['case'] == 'baseline']
                scenario_lines = cong_data[cong_data['case'] == 'scenario']
                
                x = np.arange(len(baseline_lines))
                width = 0.35
                
                ax.bar(x - width/2, baseline_lines['mean_loading']*100, width, 
                       label='Bază', alpha=0.8, color='#3498db')
                ax.bar(x + width/2, scenario_lines['mean_loading']*100, width, 
                       label='Stres', alpha=0.8, color='#e74c3c')
                
                ax.set_xlabel('Linie de Transmisie', fontsize=12)
                ax.set_ylabel('Încărcare Medie (%)', fontsize=12)
                ax.set_title('Congestie Linii: Bază vs. Stres', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels([f"Linia {asset}" for asset in baseline_lines['asset']])
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                ax.axhline(y=90, color='r', linestyle='--', alpha=0.5, label='Limită Critică')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}").pack()
    
    def create_tab_pret(self):
        """Tab 5: Preț Marginal"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💹 Preț")
        
        try:
            price_data = self.data.get('lmp_summary_ro')
            if price_data is not None and len(price_data) > 0:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                # Detectează coloanele disponibile
                available_cols = price_data.columns.tolist()
                metrics = []
                metric_labels = []
                
                # Mapare coloane cu etichete
                col_map = {
                    'mean_lmp': 'Medie', 'mean': 'Medie', 'avg_lmp': 'Medie',
                    'p95_lmp': 'P95', 'p95': 'P95',
                    'max_lmp': 'Max', 'max': 'Max', 'maximum': 'Max'
                }
                
                for col, label in col_map.items():
                    if col in available_cols:
                        metrics.append(col)
                        metric_labels.append(label)
                
                if not metrics:
                    ttk.Label(frame, text="✗ Coloane preț nu găsite în date").pack()
                    return
                
                baseline_prices = []
                scenario_prices = []
                
                for metric in metrics:
                    try:
                        baseline_val = price_data[price_data['case'] == 'baseline'][metric].values
                        scenario_val = price_data[price_data['case'] == 'scenario'][metric].values
                        
                        if len(baseline_val) > 0 and len(scenario_val) > 0:
                            baseline_prices.append(baseline_val[0])
                            scenario_prices.append(scenario_val[0])
                    except:
                        pass
                
                if not baseline_prices:
                    ttk.Label(frame, text="✗ Date preț insuficiente").pack()
                    return
                
                x = np.arange(len(metric_labels))
                width = 0.35
                
                ax.bar(x - width/2, baseline_prices, width, label='Bază', alpha=0.8, color='#2ecc71')
                ax.bar(x + width/2, scenario_prices, width, label='Stres', alpha=0.8, color='#e74c3c')
                
                ax.set_ylabel('Preț (EUR/MWh)', fontsize=12)
                ax.set_title('Preț Marginal Local România', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(metric_labels)
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(frame, text="✗ Fișier lmp_summary_ro.csv nu găsit").pack()
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {str(e)[:100]}").pack()
    
    def create_tab_date_brute(self):
        """Tab 6: Date Brute"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📋 Date Brute")
        
        # Selector fișier
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selector_frame, text="Selectați fișier CSV:").pack(side=tk.LEFT, padx=5)
        
        self.file_selector = ttk.Combobox(selector_frame, 
                                         values=list(self.data.keys()),
                                         state="readonly", width=30)
        self.file_selector.pack(side=tk.LEFT, padx=5)
        self.file_selector.bind("<<ComboboxSelected>>", self.display_data)
        
        if self.data:
            self.file_selector.current(0)
        
        # Text widget pentru date
        self.data_text = scrolledtext.ScrolledText(frame, height=20, width=120)
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Afișează date inițiale
        if self.data:
            self.display_data(None)
    
    def display_data(self, event):
        """Afișează date CSV în tabel"""
        selected = self.file_selector.get()
        if selected in self.data:
            df = self.data[selected]
            self.data_text.delete('1.0', tk.END)
            self.data_text.insert('1.0', df.to_string(index=False))
    
    def export_data(self):
        """Exportă date selectate la CSV"""
        selected = self.file_selector.get()
        if selected in self.data:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"{selected}_export.csv"
            )
            if filepath:
                self.data[selected].to_csv(filepath, index=False)
                messagebox.showinfo("Succes", f"Fișier exportat:\n{filepath}")
    
    def show_help(self):
        """Afișează ajutor"""
        help_text = """
DASHBOARD SCENARII ENERGIE - ROMÂNIA

Tabulații Disponibile:
1. 📊 REZUMAT - Metrici principale și grafic comparativ
2. 💰 COSTURI - Analiza cost total sistem
3. ⚡ GENERARE - Mix energetic per tehnologie
4. 🔌 CONGESTIE - Încărcare linii de transmisie
5. 💹 PREȚ - Preț marginal local România
6. 📋 DATE BRUTE - Tabel cu date CSV complete

Butoane:
- 🔄 Reîncarcă Date: Reîncarcă fișierele CSV din disc
- 💾 Export CSV: Salvează date selectate
- ❓ Ajutor: Afișează acest mesaj

Note:
- Datele trebuie să existe în: results/romania-2020-winter-stress-comparison/
- Toate graficele compară scenariul de BAZĂ cu scenariul de STRES
- Preț în EUR, Energie în MWh, Putere în MW
        """
        messagebox.showinfo("Ajutor", help_text)

def main():
    root = tk.Tk()
    
    # Setare stil
    style = ttk.Style()
    style.theme_use('clam')
    
    app = DashboardRomania(root)
    root.mainloop()

if __name__ == "__main__":
    main()
