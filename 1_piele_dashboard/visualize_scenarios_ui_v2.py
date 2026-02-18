#!/usr/bin/env python
"""
PyPSA-Eur Romania - Dashboard de Vizualizare Scenarii v2
Program interactiv cu selecție dinamică de scenarii
Permite alegerea directoarelor de rezultate pentru analiză
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

class DashboardRomania_v2:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Scenarii Energy v2 - PyPSA-Eur România (Selecție Dinamică)")
        self.root.geometry("1600x950")
        
        # Setări default
        self.results_dir = Path("results")
        self.selected_dir = None
        self.data = {}
        self.scenario_name = "Scenariul 1"
        
        # Creare interfață cu selecție
        self.create_ui()
        self.scan_scenarios()
        
    def scan_scenarios(self):
        """Scannează directorul results pentru scenarii disponibile"""
        self.available_scenarios = []
        
        if not self.results_dir.exists():
            return
        
        try:
            # Cauta directoare cu CSV-uri la diferite niveluri
            for main_dir in sorted(self.results_dir.iterdir(), key=lambda x: x.name, reverse=True):
                if not main_dir.is_dir():
                    continue
                
                scenario_name = main_dir.name
                
                # Cazul 1: CSV-uri direct în folder-ul principal
                csv_files_direct = list(main_dir.glob("*.csv"))
                if csv_files_direct:
                    self.available_scenarios.append(scenario_name)
                    continue
                
                # Cazul 2: CSV-uri în subfolders (*comparison*, csvs, Export, etc.)
                found_csv = False
                for subfolder_pattern in ["*comparison*", "csvs", "export*", "output*", "result*"]:
                    subfolders = list(main_dir.glob(subfolder_pattern))
                    for subfolder in subfolders:
                        if subfolder.is_dir():
                            csv_files = list(subfolder.glob("*.csv"))
                            if csv_files:
                                scenario_path = f"{scenario_name}/{subfolder.name}"
                                if scenario_path not in self.available_scenarios:
                                    self.available_scenarios.append(scenario_path)
                                found_csv = True
                
                # Cazul 3: Cauta recursiv în orice subfolder cu CSV-uri
                if not found_csv:
                    for subfolder in main_dir.rglob("*.csv"):
                        rel_path = subfolder.parent.relative_to(self.results_dir)
                        scenario_path = str(rel_path)
                        if scenario_path not in self.available_scenarios:
                            self.available_scenarios.append(scenario_path)
                        break  # Doar prima gasitura pe scenario
            
            # Sortare descrescătoare (ultimele adăugate pe top)
            self.available_scenarios.sort(reverse=True)
            
            # Update dropdown
            if self.available_scenarios:
                self.scenario_dropdown['values'] = self.available_scenarios
                self.status_var.set(f"✅ Găsite {len(self.available_scenarios)} scenarii disponibile")
            else:
                self.status_var.set("⚠️ Niciun scenariu cu CSV-uri găsit în results/")
        
        except Exception as e:
            self.status_var.set(f"❌ Eroare la scan: {str(e)[:50]}")
    
    def create_ui(self):
        """Creează interfața"""
        # ===== PANOU SELECȚIE (TOP) =====
        selection_frame = ttk.LabelFrame(self.root, text="🎯 Selecție Scenariu", padding=10)
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Row 1: Selector scenariu
        row1 = ttk.Frame(selection_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Selectați scenariu:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.scenario_dropdown = ttk.Combobox(row1, width=50, state="readonly")
        self.scenario_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.scenario_dropdown.bind("<<ComboboxSelected>>", self.on_scenario_selected)
        
        ttk.Button(row1, text="📂 Cauta Manual", command=self.browse_directory).pack(side=tk.LEFT, padx=2)
        
        # Row 2: Nume personalizat
        row2 = ttk.Frame(selection_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Nume scenariu:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.scenario_name_entry = ttk.Entry(row2, width=40)
        self.scenario_name_entry.pack(side=tk.LEFT, padx=5)
        self.scenario_name_entry.insert(0, self.scenario_name)
        
        ttk.Button(row2, text="🔄 Reîncarcă", command=self.load_selected_scenario).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="🔄 Reîncarcă Sarcini", command=self.scan_scenarios).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="❓ Ajutor", command=self.show_help).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_var = tk.StringVar(value="⏳ Așteptând selecție scenariu...")
        status_bar = ttk.Label(selection_frame, textvariable=self.status_var, 
                              font=("Arial", 9, "italic"), foreground="blue")
        status_bar.pack(fill=tk.X, pady=5)
        
        # ===== TABURI (MAIN) =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Construiește taburi
        self.create_tab_resumat()
        self.create_tab_costuri()
        self.create_tab_generare()
        self.create_tab_congestie()
        self.create_tab_pret()
        self.create_tab_date_brute()
        
    def browse_directory(self):
        """Permite select manual al direcotorului"""
        dir_path = filedialog.askdirectory(title="Selectați director cu fișiere CSV")
        if dir_path:
            self.selected_dir = Path(dir_path)
            self.scenario_dropdown.set(str(self.selected_dir))
            self.load_selected_scenario()
    
    def on_scenario_selected(self, event=None):
        """Se apelează când e selectat un scenariu"""
        selected = self.scenario_dropdown.get()
        if selected:
            self.selected_dir = self.results_dir / selected
            self.load_selected_scenario()
    
    def load_selected_scenario(self):
        """Încarcă datele din scenariul selectat"""
        if not self.selected_dir or not self.selected_dir.exists():
            messagebox.showwarning("Eroare", "Director nevalid!")
            self.status_var.set("❌ Director nevalid")
            return
        
        try:
            self.data = {}
            csv_files = list(self.selected_dir.glob("*.csv"))
            
            if not csv_files:
                messagebox.showwarning("Atenție", f"Nu s-au găsit fișiere CSV în:\n{self.selected_dir}")
                self.status_var.set("❌ Nicio fișier CSV găsit")
                return
            
            for csv_file in csv_files:
                self.data[csv_file.stem] = pd.read_csv(csv_file)
            
            # Actualizează nume scenariu din entry
            self.scenario_name = self.scenario_name_entry.get() or str(self.selected_dir.name)
            
            # Detectează formatul datelor
            data_format = self.detect_data_format()
            self.status_var.set(f"✅ Încărcate {len(csv_files)} fișiere - {self.scenario_name} [{data_format}]")
            messagebox.showinfo("Succes", f"Încărcate {len(csv_files)} fișiere CSV pentru:\n{self.scenario_name}\n\nFormat: {data_format}")
            
            # Reîncarcă taburile
            self.refresh_all_tabs()
        
        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la încărcare:\n{e}")
            self.status_var.set(f"❌ Eroare: {str(e)[:50]}")
    
    def detect_data_format(self):
        """Detectează formatul datelor (NEW vs OLD)"""
        # Formatul NEW: are system_cost_comparison.csv  
        if 'system_cost_comparison' in self.data:
            return "FORMAT NOU (Report)"
        
        # Formatul OLD: are costs.csv, energy.csv, etc.
        if 'costs' in self.data and 'energy' in self.data:
            return "FORMAT LEGACY (Rezultate native)"
        
        return "FORMAT NERECUNOSCUT"
    
    def refresh_all_tabs(self):
        """Reîncarcă conținutul tuturor tabulelor"""
        # Șterge taburi vechi
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        # Reconstruiește taburi
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
        
        title_label = ttk.Label(left, text=f"REZUMAT - {self.scenario_name}", 
                               font=("Arial", 14, "bold", "underline"))
        title_label.pack(anchor=tk.W)
        
        metrics_frame = ttk.LabelFrame(left, text="Metrici Disponibile", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        try:
            # Detectează format
            data_format = self.detect_data_format()
            
            if "NOU" in data_format:
                # FORMAT NEW - Use comparison data
                cost_data = self.data.get('system_cost_comparison')
                if cost_data is not None and len(cost_data) > 0:
                    baseline_cost = cost_data.iloc[0].get('baseline_total_system_cost_eur', 0)
                    scenario_cost = cost_data.iloc[0].get('scenario_total_system_cost_eur', 0)
                    delta = scenario_cost - baseline_cost
                    delta_pct = (delta / baseline_cost * 100) if baseline_cost > 0 else 0
                    
                    metrics = [
                        ("💶 Cost Bază", f"€{baseline_cost/1e9:.2f}B"),
                        ("💶 Cost Scenariu", f"€{scenario_cost/1e9:.2f}B"),
                        ("📈 Delta", f"€{delta/1e9:.2f}B ({delta_pct:+.1f}%)"),
                    ]
                    
                    for label, value in metrics:
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=5)
                        ttk.Label(row, text=label, width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                        ttk.Label(row, text=value, font=("Arial", 11, "bold"), foreground="darkblue").pack(side=tk.LEFT)
                
                ens_data = self.data.get('ens_summary')
                if ens_data is not None and len(ens_data) > 0:
                    ttk.Separator(metrics_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
                    
                    ens_baseline = ens_data[ens_data['case'] == 'baseline'].iloc[0] if len(ens_data) > 0 else None
                    ens_scenario = ens_data[ens_data['case'] == 'scenario'].iloc[0] if len(ens_data) > 1 else ens_data.iloc[0]
                    
                    if ens_baseline is not None:
                        metrics2 = [
                            ("⚡ ENS Bază", f"{ens_baseline.get('ens_mwh', 0):.0f} MWh"),
                            ("⚡ ENS Scenariu", f"{ens_scenario.get('ens_mwh', 0):.0f} MWh"),
                            ("⏱️ Ore Deconectare", f"{ens_scenario.get('hours_with_shedding', 0):.0f}h"),
                            ("📊 Max Deconectare", f"{ens_scenario.get('max_shedding_mw', 0):.0f} MW"),
                        ]
                        
                        for label, value in metrics2:
                            row = ttk.Frame(metrics_frame)
                            row.pack(fill=tk.X, pady=5)
                            ttk.Label(row, text=label, width=20, font=("Arial", 10)).pack(side=tk.LEFT)
                            ttk.Label(row, text=value, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
            else:
                # FORMAT OLD - Extract and display available metrics
                ttk.Label(metrics_frame, text="Format Legacy - Metrici Disponibile:", 
                         font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=10)
                
                # Extract metrics from legacy format
                try:
                    # Total energy
                    if 'energy' in self.data:
                        total_energy = self.data['energy']['0'].sum() / 1e6
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=5)
                        ttk.Label(row, text="⚡ Energie Totală", width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                        ttk.Label(row, text=f"{total_energy:.2f} TWh", font=("Arial", 11, "bold"), 
                                 foreground="darkblue").pack(side=tk.LEFT)
                    
                    # Total costs
                    if 'costs' in self.data:
                        total_costs = self.data['costs']['0'].sum() / 1e9
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=5)
                        ttk.Label(row, text="💶 Cost Total", width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                        ttk.Label(row, text=f"€{total_costs:.2f}B", font=("Arial", 11, "bold"), 
                                 foreground="darkblue").pack(side=tk.LEFT)
                    
                    # Average price
                    if 'prices' in self.data:
                        avg_price = self.data['prices']['0'].mean()
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=5)
                        ttk.Label(row, text="💹 Preț Mediu", width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                        ttk.Label(row, text=f"{avg_price:.2f} EUR/MWh", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
                    
                    # Capacity factors
                    if 'capacity_factors' in self.data:
                        avg_cf = self.data['capacity_factors']['0'].mean()
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=5)
                        ttk.Label(row, text="📊 Factor Cap. Mediu", width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                        ttk.Label(row, text=f"{avg_cf*100:.1f}%", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
                    
                    ttk.Separator(metrics_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
                    
                    # List all available files
                    ttk.Label(metrics_frame, text="Fișiere Disponibile:", 
                             font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=5)
                    
                    available_files = sorted(self.data.keys())
                    for fname in available_files:
                        row = ttk.Frame(metrics_frame)
                        row.pack(fill=tk.X, pady=2)
                        ttk.Label(row, text=f"  📄 {fname}", width=30, font=("Arial", 8)).pack(side=tk.LEFT)
                
                except Exception as e:
                    ttk.Label(metrics_frame, text=f"Eroare extragere metrici: {e}", foreground="red").pack()
        
        except Exception as e:
            ttk.Label(metrics_frame, text=f"Eroare: {e}", foreground="red").pack()
        
        # Painel dreapta - Grafic
        right = ttk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(right, text="MIX ENERGETIC", font=("Arial", 12, "bold")).pack()
        
        try:
            gen_data = self.data.get('generation_mix_mwh')
            if gen_data is not None and len(gen_data) > 0:
                fig = Figure(figsize=(6, 4), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline = gen_data[gen_data['case'] == 'baseline']
                scenario = gen_data[gen_data['case'] == 'scenario']
                
                if len(baseline) > 0 and len(scenario) > 0:
                    x = np.arange(len(baseline))
                    width = 0.35
                    
                    ax.bar(x - width/2, baseline['generation_mwh'], width, label='Bază', alpha=0.8, color='#3498db')
                    ax.bar(x + width/2, scenario['generation_mwh'], width, label='Scenariu', alpha=0.8, color='#e74c3c')
                    
                    ax.set_xlabel('Tehnologie', fontsize=10)
                    ax.set_ylabel('Generare (MWh)', fontsize=10)
                    ax.set_title(f'Mix Energetic - {self.scenario_name}', fontsize=11, fontweight='bold')
                    ax.set_xticks(x)
                    ax.set_xticklabels(baseline['carrier'], rotation=45, ha='right', fontsize=8)
                    ax.legend(fontsize=10)
                    ax.grid(True, alpha=0.3)
                    fig.tight_layout()
                    
                    canvas = FigureCanvasTkAgg(fig, master=right)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(right, text=f"Eroare grafic: {e}", foreground="red").pack()
    
    def create_tab_costuri(self):
        """Tab 2: Analiza Costuri"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💰 Costuri")
        
        data_format = self.detect_data_format()
        
        if "LEGACY" in data_format:
            # Format Legacy - Extract costs from costs.csv
            try:
                costs_data = self.data.get('costs')
                if costs_data is not None and len(costs_data) > 0:
                    # Pivot to get total cost
                    total_cost = costs_data[['0']].sum().values[0] if '0' in costs_data.columns else 0
                    
                    fig = Figure(figsize=(10, 6), dpi=80)
                    ax = fig.add_subplot(111)
                    
                    # Get costs by component
                    if 'component' in costs_data.columns:
                        costs_by_comp = costs_data.groupby('component')['0'].sum().sort_values(ascending=False)
                        
                        ax.barh(range(len(costs_by_comp)), costs_by_comp.values / 1e9, color='#3498db', alpha=0.8)
                        ax.set_yticks(range(len(costs_by_comp)))
                        ax.set_yticklabels(costs_by_comp.index, fontsize=11)
                        ax.set_xlabel('Cost (Miliarde EUR)', fontsize=12)
                        ax.set_title(f'Cost pe Componentă - {self.scenario_name}', fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3, axis='x')
                        
                        # Add values on bars
                        for i, v in enumerate(costs_by_comp.values / 1e9):
                            ax.text(v, i, f' €{v:.3f}B', va='center', fontsize=10)
                    
                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            except Exception as e:
                ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
            return
        
        try:
            cost_data = self.data.get('system_cost_comparison')
            if cost_data is not None and len(cost_data) > 0:
                baseline_cost = cost_data.iloc[0].get('baseline_total_system_cost_eur', 0)
                scenario_cost = cost_data.iloc[0].get('scenario_total_system_cost_eur', 0)
                
                fig = Figure(figsize=(10, 6), dpi=80)
                
                ax1 = fig.add_subplot(121)
                cases = ['Bază', self.scenario_name]
                costs = [baseline_cost/1e9, scenario_cost/1e9]
                colors = ['#2ecc71', '#e74c3c']
                bars = ax1.bar(cases, costs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
                ax1.set_ylabel('Cost (Miliarde EUR)', fontsize=11)
                ax1.set_title('Cost Total Sistem', fontsize=12, fontweight='bold')
                ax1.grid(True, alpha=0.3, axis='y')
                
                for bar, cost in zip(bars, costs):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'€{cost:.2f}B', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                ax2 = fig.add_subplot(122)
                delta = scenario_cost - baseline_cost
                delta_pct = (delta / baseline_cost * 100) if baseline_cost > 0 else 0
                ax2.bar(['Delta'], [delta/1e9], color='#e74c3c' if delta > 0 else '#2ecc71', 
                       alpha=0.7, edgecolor='black', linewidth=2)
                ax2.set_ylabel('Cost Adiţional (Miliarde EUR)', fontsize=11)
                ax2.set_title(f'Cost {self.scenario_name} vs. Bază\n({delta_pct:+.1f}%)', 
                             fontsize=12, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
                ax2.text(0, delta/1e9, f'€{delta/1e9:.2f}B', ha='center', 
                        va='bottom' if delta > 0 else 'top', fontsize=10, fontweight='bold')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
            cost_data = self.data.get('system_cost_comparison')
            if cost_data is not None and len(cost_data) > 0:
                baseline_cost = cost_data.iloc[0].get('baseline_total_system_cost_eur', 0)
                scenario_cost = cost_data.iloc[0].get('scenario_total_system_cost_eur', 0)
                
                fig = Figure(figsize=(10, 6), dpi=80)
                
                ax1 = fig.add_subplot(121)
                cases = ['Bază', self.scenario_name]
                costs = [baseline_cost/1e9, scenario_cost/1e9]
                colors = ['#2ecc71', '#e74c3c']
                bars = ax1.bar(cases, costs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
                ax1.set_ylabel('Cost (Miliarde EUR)', fontsize=11)
                ax1.set_title('Cost Total Sistem', fontsize=12, fontweight='bold')
                ax1.grid(True, alpha=0.3, axis='y')
                
                for bar, cost in zip(bars, costs):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'€{cost:.2f}B', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                ax2 = fig.add_subplot(122)
                delta = scenario_cost - baseline_cost
                delta_pct = (delta / baseline_cost * 100) if baseline_cost > 0 else 0
                ax2.bar(['Delta'], [delta/1e9], color='#e74c3c' if delta > 0 else '#2ecc71', 
                       alpha=0.7, edgecolor='black', linewidth=2)
                ax2.set_ylabel('Cost Adiţional (Miliarde EUR)', fontsize=11)
                ax2.set_title(f'Cost {self.scenario_name} vs. Bază\n({delta_pct:+.1f}%)', 
                             fontsize=12, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
                ax2.text(0, delta/1e9, f'€{delta/1e9:.2f}B', ha='center', 
                        va='bottom' if delta > 0 else 'top', fontsize=10, fontweight='bold')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
    
    def create_tab_generare(self):
        """Tab 3: Analiza Generare"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚡ Generare")
        
        data_format = self.detect_data_format()
        
        if "LEGACY" in data_format:
            # Format Legacy - Use energy.csv
            try:
                energy_data = self.data.get('energy')
                if energy_data is not None and len(energy_data) > 0:
                    fig = Figure(figsize=(10, 6), dpi=80)
                    ax = fig.add_subplot(111)
                    
                    # Parse energy data by carrier
                    if 'carrier' in energy_data.columns:
                        energy_by_carrier = energy_data.groupby('carrier')['0'].sum().sort_values(ascending=False)
                        
                        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
                        ax.bar(range(len(energy_by_carrier)), energy_by_carrier.values / 1e6, 
                              color=colors[:len(energy_by_carrier)], alpha=0.8, edgecolor='black')
                        ax.set_xticks(range(len(energy_by_carrier)))
                        ax.set_xticklabels(energy_by_carrier.index, rotation=45, ha='right', fontsize=11)
                        ax.set_ylabel('Energie (TWh)', fontsize=12)
                        ax.set_title(f'Producție Energetică pe Tehnologie - {self.scenario_name}', 
                                    fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3, axis='y')
                        
                        # Add values on bars
                        for i, v in enumerate(energy_by_carrier.values / 1e6):
                            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            except Exception as e:
                ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
            return
        
        try:
            gen_data = self.data.get('generation_mix_mwh')
            if gen_data is not None and len(gen_data) > 0:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline = gen_data[gen_data['case'] == 'baseline'].set_index('carrier')
                scenario = gen_data[gen_data['case'] == 'scenario'].set_index('carrier')
                
                x = np.arange(len(baseline))
                width = 0.35
                
                ax.bar(x - width/2, baseline['generation_mwh'], width, label='Bază', alpha=0.8, color='#3498db')
                ax.bar(x + width/2, scenario['generation_mwh'], width, label=self.scenario_name, 
                       alpha=0.8, color='#e74c3c')
                
                ax.set_xlabel('Technologie', fontsize=12)
                ax.set_ylabel('Generare (MWh)', fontsize=12)
                ax.set_title(f'Mix Energetic: Bază vs. {self.scenario_name}', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(baseline.index, rotation=45, ha='right', fontsize=10)
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
            gen_data = self.data.get('generation_mix_mwh')
            if gen_data is not None and len(gen_data) > 0:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline = gen_data[gen_data['case'] == 'baseline'].set_index('carrier')
                scenario = gen_data[gen_data['case'] == 'scenario'].set_index('carrier')
                
                x = np.arange(len(baseline))
                width = 0.35
                
                ax.bar(x - width/2, baseline['generation_mwh'], width, label='Bază', alpha=0.8, color='#3498db')
                ax.bar(x + width/2, scenario['generation_mwh'], width, label=self.scenario_name, 
                       alpha=0.8, color='#e74c3c')
                
                ax.set_xlabel('Technologie', fontsize=12)
                ax.set_ylabel('Generare (MWh)', fontsize=12)
                ax.set_title(f'Mix Energetic: Bază vs. {self.scenario_name}', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(baseline.index, rotation=45, ha='right', fontsize=10)
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
    
    def create_tab_congestie(self):
        """Tab 4: Congestie Linii"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔌 Congestie")
        
        data_format = self.detect_data_format()
        
        if "LEGACY" in data_format:
            ttk.Label(frame, text="\n⚠️ Format Legacy - Date Indisponibile\n\n"
                     "Dimensionarea liniilor nu este disponibilă în\nformatul Legacy (rezultate native).\n\n"
                     "Fișierele disponibile:\n" + ", ".join(sorted(self.data.keys())[:8]),
                     font=("Arial", 11), justify=tk.CENTER, foreground="orange").pack(pady=50)
            return
        
        try:
            cong_data = self.data.get('interconnector_flow_congestion')
            if cong_data is not None and len(cong_data) > 0:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                baseline_lines = cong_data[cong_data['case'] == 'baseline']
                scenario_lines = cong_data[cong_data['case'] == 'scenario']
                
                x = np.arange(len(baseline_lines))
                width = 0.35
                
                ax.bar(x - width/2, baseline_lines['mean_loading']*100, width, 
                       label='Bază', alpha=0.8, color='#3498db')
                ax.bar(x + width/2, scenario_lines['mean_loading']*100, width, 
                       label=self.scenario_name, alpha=0.8, color='#e74c3c')
                
                ax.set_xlabel('Linie de Transmisie', fontsize=12)
                ax.set_ylabel('Încărcare Medie (%)', fontsize=12)
                ax.set_title(f'Congestie Linii: Bază vs. {self.scenario_name}', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels([f"L{i+1}" for i in range(len(baseline_lines))], fontsize=10)
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3, axis='y')
                ax.axhline(y=90, color='r', linestyle='--', alpha=0.5, linewidth=2, label='Critică')
                ax.set_ylim(0, max(np.max(baseline_lines['mean_loading']*100)*1.2, 100))
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
    
    def create_tab_pret(self):
        """Tab 5: Preț Marginal"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💹 Preț")
        
        data_format = self.detect_data_format()
        
        if "LEGACY" in data_format:
            # Format Legacy - Use prices.csv or weighted_prices.csv
            try:
                prices_data = self.data.get('prices') or self.data.get('weighted_prices')
                if prices_data is not None and len(prices_data) > 0:
                    fig = Figure(figsize=(10, 6), dpi=80)
                    ax = fig.add_subplot(111)
                    
                    # Extract price statistics
                    if '0' in prices_data.columns:
                        price_values = prices_data['0'].dropna()
                        
                        stats = {
                            'Medie': price_values.mean(),
                            'Mediana': price_values.median(),
                            'Min': price_values.min(),
                            'Max': price_values.max(),
                            'P95': price_values.quantile(0.95)
                        }
                        
                        ax.bar(stats.keys(), stats.values(), color='#3498db', alpha=0.8, edgecolor='black', linewidth=2)
                        ax.set_ylabel('Preț (EUR/MWh)', fontsize=12)
                        ax.set_title(f'Statistici Preț Marginal - {self.scenario_name}', 
                                    fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3, axis='y')
                        
                        # Add values on bars
                        for i, (k, v) in enumerate(stats.items()):
                            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    
                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    ttk.Label(frame, text="\n⚠️ Fișier preț indisponibil\n\n"
                             f"Fișierele disponibile:\n" + ", ".join(sorted(self.data.keys())[:8]),
                             font=("Arial", 11), justify=tk.CENTER, foreground="orange").pack(pady=50)
            except Exception as e:
                ttk.Label(frame, text=f"Eroare: {e}", foreground="red").pack()
            return
        
        try:
            price_data = self.data.get('lmp_summary_ro')
            if price_data is not None and len(price_data) > 0:
                fig = Figure(figsize=(10, 6), dpi=80)
                ax = fig.add_subplot(111)
                
                # Detectează coloanele disponibile
                available_cols = price_data.columns.tolist()
                metrics = []
                metric_labels = []
                
                col_map = {
                    'mean_lmp': 'Medie', 'mean': 'Medie', 'avg_lmp': 'Medie',
                    'p95_lmp': 'P95', 'p95': 'P95',
                    'max_lmp': 'Max', 'max': 'Max', 'maximum': 'Max'
                }
                
                for col, label in col_map.items():
                    if col in available_cols:
                        metrics.append(col)
                        metric_labels.append(label)
                
                if not metrics or len(price_data) < 2:
                    ttk.Label(frame, text="Dată preț insuficientă", foreground="orange").pack()
                    return
                
                baseline_prices = []
                scenario_prices = []
                
                for metric in metrics:
                    try:
                        baseline_val = price_data[price_data['case'] == 'baseline'][metric].values[0]
                        scenario_val = price_data[price_data['case'] == 'scenario'][metric].values[0]
                        baseline_prices.append(baseline_val)
                        scenario_prices.append(scenario_val)
                    except:
                        pass
                
                if baseline_prices:
                    x = np.arange(len(metric_labels))
                    width = 0.35
                    
                    ax.bar(x - width/2, baseline_prices, width, label='Bază', alpha=0.8, color='#2ecc71')
                    ax.bar(x + width/2, scenario_prices, width, label=self.scenario_name, 
                           alpha=0.8, color='#e74c3c')
                    
                    ax.set_ylabel('Preț (EUR/MWh)', fontsize=12)
                    ax.set_title(f'Preț Marginal Local - {self.scenario_name}', fontsize=14, fontweight='bold')
                    ax.set_xticks(x)
                    ax.set_xticklabels(metric_labels)
                    ax.legend(fontsize=11)
                    ax.grid(True, alpha=0.3, axis='y')
                    
                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            ttk.Label(frame, text=f"Eroare: {str(e)[:80]}", foreground="red").pack()
    
    def create_tab_date_brute(self):
        """Tab 6: Date Brute"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📋 Date Brute")
        
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selector_frame, text="CSV:").pack(side=tk.LEFT, padx=5)
        
        self.file_selector = ttk.Combobox(selector_frame, 
                                         values=list(self.data.keys()),
                                         state="readonly", width=30)
        self.file_selector.pack(side=tk.LEFT, padx=5)
        self.file_selector.bind("<<ComboboxSelected>>", self.display_data)
        
        if self.data:
            self.file_selector.current(0)
        
        ttk.Button(selector_frame, text="💾 Export", command=self.export_data).pack(side=tk.LEFT, padx=2)
        
        self.data_text = scrolledtext.ScrolledText(frame, height=20, width=150, font=("Courier", 8))
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        if self.data:
            self.display_data(None)
    
    def display_data(self, event):
        """Afișează date CSV"""
        selected = self.file_selector.get()
        if selected in self.data:
            df = self.data[selected]
            self.data_text.delete('1.0', tk.END)
            self.data_text.insert('1.0', df.to_string(index=False))
    
    def export_data(self):
        """Exportă date"""
        selected = self.file_selector.get()
        if selected in self.data:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"{selected}_export.csv"
            )
            if filepath:
                self.data[selected].to_csv(filepath, index=False)
                messagebox.showinfo("Succes", f"Exportat:\n{filepath}")
    
    def show_help(self):
        """Ajutor"""
        help_text = """
DASHBOARD v2 - SELECȚIE DINAMICĂ

FUNCȚII NOI:
✓ Selectare dinamică a scenariilor din dropdown
✓ Cauta manual prin 📂 Cauta Manual
✓ Rename personalizat al scenariului
✓ Suport multiplii scenarii

WORKFLOW:
1. Dropdown → Selectează scenariu disponibil
   SAU
   📂 Cauta Manual → Browser folder

2. (Opțional) Rename în "Nume scenariu"

3. 🔄 Reîncarcă → Încarcă datele

4. Navighează taburi → Analizează metrici

TABURI:
📊 Rezumat - Metrici principale
💰 Costuri - Cost total bază vs. scenariu
⚡ Generare - Mix energetic
🔌 Congestie - Încărcare linii
💹 Preț - Preț marginal local
📋 Date Brute - Tabel CSV complet

CONTROL:
🔄 Reîncarcă - Reîncarcă datele selectate
🔄 Reîncarcă Sarcini - Scannează din nou folder results/
❓ Ajutor - Afișează acest mesaj
💾 Export - Salvează CSV selectat

DIRECTOARE SUPORTATE:
- results/[scenario]/[comparison]/
- Orice folder cu fișiere .csv
        """
        messagebox.showinfo("Ajutor Dashboard v2", help_text)

def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    
    app = DashboardRomania_v2(root)
    root.mainloop()

if __name__ == "__main__":
    main()
