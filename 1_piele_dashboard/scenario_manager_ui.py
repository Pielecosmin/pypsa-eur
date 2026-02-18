#!/usr/bin/env python
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

import yaml

from scenario_manager.config_builder import (
    build_commands,
    build_configs,
    build_working_config,
    dump_yaml,
    list_reference_baselines,
    load_template,
)
from scenario_manager.i18n import LANGUAGES, tr
from scenario_manager.results_index import load_csv_preview, parse_summary, scan_new_format_results
from scenario_manager.run_manager import RunManager
from scenario_manager.state_store import load_state, save_state
from scenario_manager.types import CommandSpec, JobRecord, JobSpec, ScenarioInputs, StressParams


class ScenarioManagerUI:
    JOB_POLL_MS = 1000
    RESULTS_POLL_MS = 5000

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.repo_root = Path(__file__).resolve().parents[1]
        self.template_path = self.repo_root / "1_piele_docs" / "scenario_template.yaml"
        self.state_path = self.repo_root / "1_piele_dashboard" / "scenario_manager_state.json"
        self.logs_dir = self.repo_root / "logs" / "planui"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.state = load_state(self.state_path)
        self.template_config = load_template(self.template_path)

        self._jobs_dirty = True
        self._job_by_id: dict[str, JobRecord] = {}
        self._result_by_name: dict[str, Path] = {}
        self._result_image: tk.PhotoImage | None = None

        ui = dict(self.state.get("ui_state", {}))
        self.lang = tk.StringVar(value=str(self.state.get("language", ui.get("language", "en"))))
        self.status = tk.StringVar(value=tr(self.lang.get(), "status_ready"))

        self.run_mode = tk.StringVar(value=str(ui.get("run_mode", "paired")))
        self.output_name = tk.StringVar(value=str(ui.get("output_name", "")))
        self.scenario_slug = tk.StringVar(value=str(ui.get("scenario_slug", "romania-winter-stress")))
        self.country = tk.StringVar(value=str(ui.get("country", "RO")))
        self.countries = tk.StringVar(value=str(ui.get("countries", "RO,BG,HU,RS")))
        self.snapshot_start = tk.StringVar(value=str(ui.get("snapshot_start", "2020-12-01")))
        self.snapshot_end = tk.StringVar(value=str(ui.get("snapshot_end", "2020-12-08")))
        self.clusters = tk.StringVar(value=str(ui.get("clusters", "10")))
        self.solver_name = tk.StringVar(value=str(ui.get("solver_name", "highs")))
        self.solver_options = tk.StringVar(value=str(ui.get("solver_options", "highs-simplex")))
        self.reference_baseline = tk.StringVar(value=str(ui.get("reference_baseline_net", "")))
        self.stress_enable = tk.BooleanVar(value=bool(ui.get("stress_enable", True)))
        self.stress_load = tk.StringVar(value=str(ui.get("stress_load_factor", "1.12")))
        self.stress_hydro = tk.StringVar(value=str(ui.get("stress_hydro_factor", "0.60")))
        self.stress_gas = tk.StringVar(value=str(ui.get("stress_gas_factor", "0.70")))
        self.scada_tight = tk.StringVar(value=str(ui.get("scada_tight_hours", "24")))
        self.scada_relaxed = tk.StringVar(value=str(ui.get("scada_relaxed_hours", "48")))
        self.scada_ramp_tight = tk.StringVar(value=str(ui.get("scada_ramp_tight", "0.10")))
        self.scada_ramp_relaxed = tk.StringVar(value=str(ui.get("scada_ramp_relaxed", "0.25")))
        self.import_zero = tk.StringVar(value=str(ui.get("import_zero_hours", "48")))
        self.import_half = tk.StringVar(value=str(ui.get("import_half_hours", "48")))
        self.import_factor = tk.StringVar(value=str(ui.get("import_half_factor", "0.5")))

        self.run_manager = RunManager(
            repo_root=self.repo_root,
            jobs=self.state.get("jobs", []),
            on_change=self._mark_jobs_dirty,
        )

        self.root.geometry("1700x980")
        self._build_ui()
        self._load_yaml(ui.get("working_yaml", ""))
        self.refresh_baseline_networks()
        self.refresh_results(force=True)
        self._refresh_texts()
        self._update_mode_widgets()

        self.root.after(self.JOB_POLL_MS, self._poll_jobs)
        self.root.after(self.RESULTS_POLL_MS, self._poll_results)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)
        self.title_label = ttk.Label(top, font=("Segoe UI", 11, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=(0, 12))
        self.lang_label = ttk.Label(top)
        self.lang_label.pack(side=tk.LEFT)
        lang_combo = ttk.Combobox(top, values=list(LANGUAGES), width=5, state="readonly", textvariable=self.lang)
        lang_combo.pack(side=tk.LEFT, padx=(4, 14))
        lang_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_lang_change())
        self.spinner_label = ttk.Label(top)
        self.spinner_label.pack(side=tk.LEFT, padx=(0, 4))
        self.spinner = ttk.Progressbar(top, mode="indeterminate", length=140)
        self.spinner.pack(side=tk.LEFT)
        ttk.Label(top, textvariable=self.status).pack(side=tk.RIGHT)

        self.main_tabs = ttk.Notebook(self.root)
        self.main_tabs.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.tab_builder = ttk.Frame(self.main_tabs)
        self.tab_runs = ttk.Frame(self.main_tabs)
        self.tab_results = ttk.Frame(self.main_tabs)
        self.main_tabs.add(self.tab_builder, text="")
        self.main_tabs.add(self.tab_runs, text="")
        self.main_tabs.add(self.tab_results, text="")
        self._build_builder_tab()
        self._build_runs_tab()
        self._build_results_tab()

