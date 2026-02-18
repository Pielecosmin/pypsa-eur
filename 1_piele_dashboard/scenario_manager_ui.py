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
        self._saved_selected_result = str(ui.get("selected_result", ""))
        self._saved_main_tab = str(ui.get("main_tab", "builder"))
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
        tab_map = {"builder": self.tab_builder, "runs": self.tab_runs, "results": self.tab_results}
        self.main_tabs.select(tab_map.get(self._saved_main_tab, self.tab_builder))

    def _build_builder_tab(self) -> None:
        form = ttk.LabelFrame(self.tab_builder, padding=8)
        form.pack(fill=tk.X, pady=(0, 8))
        self.builder_frame = form

        rows = [
            ("mode", self.run_mode, ["paired", "single"]),
            ("output", self.output_name, None),
            ("slug", self.scenario_slug, None),
            ("country", self.country, None),
            ("countries", self.countries, None),
            ("start", self.snapshot_start, None),
            ("end", self.snapshot_end, None),
            ("clusters", self.clusters, None),
            ("solver", self.solver_name, None),
            ("solver_opts", self.solver_options, None),
        ]
        self.form_labels: dict[str, ttk.Label] = {}
        for idx, (name, var, values) in enumerate(rows):
            lbl = ttk.Label(form)
            lbl.grid(row=idx // 2, column=(idx % 2) * 2, sticky="w", padx=4, pady=4)
            self.form_labels[name] = lbl
            if values:
                cbox = ttk.Combobox(form, values=values, state="readonly", textvariable=var, width=30)
                cbox.grid(row=idx // 2, column=(idx % 2) * 2 + 1, sticky="ew", padx=4, pady=4)
                cbox.bind("<<ComboboxSelected>>", lambda _e: self._update_mode_widgets())
                self.mode_combo = cbox
            else:
                ttk.Entry(form, textvariable=var, width=34).grid(
                    row=idx // 2, column=(idx % 2) * 2 + 1, sticky="ew", padx=4, pady=4
                )

        self.reference_label = ttk.Label(form)
        self.reference_label.grid(row=5, column=0, sticky="w", padx=4, pady=4)
        self.reference_combo = ttk.Combobox(form, textvariable=self.reference_baseline, width=64)
        self.reference_combo.grid(row=5, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
        self.refresh_baseline_btn = ttk.Button(form, command=self.refresh_baseline_networks)
        self.refresh_baseline_btn.grid(row=5, column=3, sticky="ew", padx=4, pady=4)

        self.stress_toggle = ttk.Checkbutton(form, variable=self.stress_enable)
        self.stress_toggle.grid(row=6, column=0, sticky="w", padx=4, pady=4)
        stress_fields = [
            ("stress_load", self.stress_load),
            ("stress_hydro", self.stress_hydro),
            ("stress_gas", self.stress_gas),
            ("scada_tight", self.scada_tight),
            ("scada_relaxed", self.scada_relaxed),
            ("scada_ramp_tight", self.scada_ramp_tight),
            ("scada_ramp_relaxed", self.scada_ramp_relaxed),
            ("import_zero", self.import_zero),
            ("import_half", self.import_half),
            ("import_factor", self.import_factor),
        ]
        self.stress_labels: dict[str, ttk.Label] = {}
        for idx, (name, var) in enumerate(stress_fields):
            row = 6 + idx // 3
            col = (idx % 3) * 2 + 1
            lbl = ttk.Label(form)
            lbl.grid(row=row, column=col, sticky="w", padx=4, pady=4)
            self.stress_labels[name] = lbl
            ttk.Entry(form, textvariable=var, width=12).grid(row=row, column=col + 1, sticky="w", padx=4, pady=4)
        for col in range(4):
            form.columnconfigure(col, weight=1)

        actions = ttk.Frame(self.tab_builder)
        actions.pack(fill=tk.X, pady=(0, 6))
        self.btn_apply_controls = ttk.Button(actions, command=self.apply_controls_to_yaml)
        self.btn_apply_controls.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_apply_yaml = ttk.Button(actions, command=self.apply_yaml_to_controls)
        self.btn_apply_yaml.pack(side=tk.LEFT, padx=(0, 6))

        panes = ttk.Panedwindow(self.tab_builder, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)
        self.frame_working = ttk.LabelFrame(panes, padding=6)
        self.frame_template = ttk.LabelFrame(panes, padding=6)
        panes.add(self.frame_working, weight=1)
        panes.add(self.frame_template, weight=1)
        self.working_yaml = scrolledtext.ScrolledText(self.frame_working, wrap=tk.NONE, height=18)
        self.working_yaml.pack(fill=tk.BOTH, expand=True)
        self.template_yaml = scrolledtext.ScrolledText(self.frame_template, wrap=tk.NONE, height=18)
        self.template_yaml.pack(fill=tk.BOTH, expand=True)
        self.template_yaml.configure(state="disabled")

    def _build_runs_tab(self) -> None:
        submit = ttk.LabelFrame(self.tab_runs, padding=8)
        submit.pack(fill=tk.X, pady=(0, 8))
        self.runs_submit_frame = submit
        ttk.Label(submit, textvariable=self.output_name, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=6)
        ttk.Label(submit, textvariable=self.run_mode).pack(side=tk.LEFT, padx=6)
        ttk.Label(submit, textvariable=self.reference_baseline).pack(side=tk.LEFT, padx=6)
        self.btn_enqueue = ttk.Button(submit, command=self.enqueue_job)
        self.btn_enqueue.pack(side=tk.RIGHT)

        queue = ttk.LabelFrame(self.tab_runs, padding=8)
        queue.pack(fill=tk.BOTH, expand=True)
        self.runs_queue_frame = queue
        cols = ("job_id", "status", "mode", "output", "progress")
        self.tree_jobs = ttk.Treeview(queue, columns=cols, show="headings", height=15)
        for name, width in [("job_id", 170), ("status", 120), ("mode", 90), ("output", 290), ("progress", 760)]:
            self.tree_jobs.heading(name, text=name)
            self.tree_jobs.column(name, width=width, anchor="w")
        self.tree_jobs.pack(fill=tk.BOTH, expand=True)
        self.tree_jobs.bind("<<TreeviewSelect>>", lambda _e: self.on_job_selected())

        row = ttk.Frame(queue)
        row.pack(fill=tk.X, pady=(6, 0))
        self.btn_cancel = ttk.Button(row, command=self.cancel_selected_job)
        self.btn_cancel.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_refresh_jobs = ttk.Button(row, command=self.refresh_jobs_now)
        self.btn_refresh_jobs.pack(side=tk.LEFT)

        self.job_details = scrolledtext.ScrolledText(queue, height=8, wrap=tk.WORD)
        self.job_details.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        self.job_details.configure(state="disabled")

    def _build_results_tab(self) -> None:
        panes = ttk.Panedwindow(self.tab_results, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=0)
        panes.add(right, weight=1)

        self.btn_refresh_results = ttk.Button(left, command=lambda: self.refresh_results(force=True))
        self.btn_refresh_results.pack(fill=tk.X, pady=(0, 6))
        self.list_results = tk.Listbox(left, width=42, height=28)
        self.list_results.pack(fill=tk.BOTH, expand=True)
        self.list_results.bind("<<ListboxSelect>>", lambda _e: self.on_result_selected())

        self.result_tabs = ttk.Notebook(right)
        self.result_tabs.pack(fill=tk.BOTH, expand=True)
        self.tab_summary = ttk.Frame(self.result_tabs)
        self.tab_csv = ttk.Frame(self.result_tabs)
        self.tab_fig = ttk.Frame(self.result_tabs)
        self.tab_assume = ttk.Frame(self.result_tabs)
        self.result_tabs.add(self.tab_summary, text="")
        self.result_tabs.add(self.tab_csv, text="")
        self.result_tabs.add(self.tab_fig, text="")
        self.result_tabs.add(self.tab_assume, text="")

        self.summary_text = scrolledtext.ScrolledText(self.tab_summary, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.configure(state="disabled")

        csv_row = ttk.Frame(self.tab_csv)
        csv_row.pack(fill=tk.X, pady=(0, 4))
        self.combo_csv = ttk.Combobox(csv_row, state="readonly")
        self.combo_csv.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo_csv.bind("<<ComboboxSelected>>", lambda _e: self.on_csv_selected())
        self.tree_csv = ttk.Treeview(self.tab_csv, show="headings")
        self.tree_csv.pack(fill=tk.BOTH, expand=True)

        fig_panes = ttk.Panedwindow(self.tab_fig, orient=tk.HORIZONTAL)
        fig_panes.pack(fill=tk.BOTH, expand=True)
        fig_left = ttk.Frame(fig_panes, padding=4)
        fig_right = ttk.Frame(fig_panes, padding=4)
        fig_panes.add(fig_left, weight=0)
        fig_panes.add(fig_right, weight=1)
        self.list_fig = tk.Listbox(fig_left, width=34)
        self.list_fig.pack(fill=tk.BOTH, expand=True)
        self.list_fig.bind("<<ListboxSelect>>", lambda _e: self.on_figure_selected())
        self.fig_label = ttk.Label(fig_right)
        self.fig_label.pack(fill=tk.BOTH, expand=True)

        self.assume_text = scrolledtext.ScrolledText(self.tab_assume, wrap=tk.WORD)
        self.assume_text.pack(fill=tk.BOTH, expand=True)
        self.assume_text.configure(state="disabled")

    def _on_lang_change(self) -> None:
        self._refresh_texts()
        self._save_state()

    def _refresh_texts(self) -> None:
        lang = self.lang.get()
        self.root.title(tr(lang, "app_title"))
        self.title_label.configure(text=tr(lang, "app_title"))
        self.lang_label.configure(text=tr(lang, "language"))
        self.spinner_label.configure(text=tr(lang, "spinner_idle"))
        self.main_tabs.tab(self.tab_builder, text=tr(lang, "nav_builder"))
        self.main_tabs.tab(self.tab_runs, text=tr(lang, "nav_runs"))
        self.main_tabs.tab(self.tab_results, text=tr(lang, "nav_results"))
        self.builder_frame.configure(text=tr(lang, "builder_section_core"))
        label_map = {
            "mode": "mode_label",
            "output": "output_name",
            "slug": "scenario_slug",
            "country": "country",
            "countries": "countries",
            "start": "snapshot_start",
            "end": "snapshot_end",
            "clusters": "clusters",
            "solver": "solver_name",
            "solver_opts": "solver_options",
        }
        for key, trans in label_map.items():
            self.form_labels[key].configure(text=tr(lang, trans))
        self.reference_label.configure(text=tr(lang, "reference_baseline"))
        self.refresh_baseline_btn.configure(text=tr(lang, "refresh_baselines"))
        self.stress_toggle.configure(text=tr(lang, "stress_enable"))
        stress_map = {
            "stress_load": "stress_load",
            "stress_hydro": "stress_hydro",
            "stress_gas": "stress_gas",
            "scada_tight": "scada_tight",
            "scada_relaxed": "scada_relaxed",
            "scada_ramp_tight": "scada_ramp_tight",
            "scada_ramp_relaxed": "scada_ramp_relaxed",
            "import_zero": "import_zero",
            "import_half": "import_half",
            "import_factor": "import_factor",
        }
        for key, trans in stress_map.items():
            self.stress_labels[key].configure(text=tr(lang, trans))
        self.btn_apply_controls.configure(text=tr(lang, "apply_controls_to_yaml"))
        self.btn_apply_yaml.configure(text=tr(lang, "apply_yaml_to_controls"))
        self.frame_working.configure(text=tr(lang, "working_yaml"))
        self.frame_template.configure(text=tr(lang, "template_read_only"))
        self.runs_submit_frame.configure(text=tr(lang, "runs_submit"))
        self.btn_enqueue.configure(text=tr(lang, "runs_submit"))
        self.runs_queue_frame.configure(text=tr(lang, "runs_queue"))
        self.btn_cancel.configure(text=tr(lang, "runs_cancel"))
        self.btn_refresh_jobs.configure(text=tr(lang, "runs_refresh"))
        self.btn_refresh_results.configure(text=tr(lang, "results_refresh"))
        self.result_tabs.tab(self.tab_summary, text=tr(lang, "results_summary"))
        self.result_tabs.tab(self.tab_csv, text=tr(lang, "results_csv"))
        self.result_tabs.tab(self.tab_fig, text=tr(lang, "results_figures"))
        self.result_tabs.tab(self.tab_assume, text=tr(lang, "results_assumptions"))

    def _load_yaml(self, saved: str) -> None:
        working = saved if str(saved).strip() else dump_yaml(self.template_config)
        self.working_yaml.delete("1.0", tk.END)
        self.working_yaml.insert("1.0", working)
        self.template_yaml.configure(state="normal")
        self.template_yaml.delete("1.0", tk.END)
        self.template_yaml.insert("1.0", self.template_path.read_text(encoding="utf-8"))
        self.template_yaml.configure(state="disabled")

    def _parse_int(self, value: str, name: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"Invalid integer for {name}: {value}") from exc

    def _parse_float(self, value: str, name: str) -> float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Invalid float for {name}: {value}") from exc

    def _collect_inputs(self) -> ScenarioInputs:
        countries = [x.strip().upper() for x in self.countries.get().split(",") if x.strip()]
        if not countries:
            countries = [self.country.get().strip().upper()]
        return ScenarioInputs(
            run_mode=self.run_mode.get().strip(),  # type: ignore[arg-type]
            output_name=self.output_name.get().strip(),
            scenario_slug=self.scenario_slug.get().strip(),
            country=self.country.get().strip().upper(),
            countries=countries,
            snapshot_start=self.snapshot_start.get().strip(),
            snapshot_end=self.snapshot_end.get().strip(),
            clusters=self._parse_int(self.clusters.get().strip(), "clusters"),
            solver_name=self.solver_name.get().strip(),
            solver_options=self.solver_options.get().strip(),
            stress_enable=bool(self.stress_enable.get()),
            stress=StressParams(
                load_factor_full_window=self._parse_float(self.stress_load.get(), "stress_load"),
                hydro_factor_full_window=self._parse_float(self.stress_hydro.get(), "stress_hydro"),
                gas_factor_first_72h=self._parse_float(self.stress_gas.get(), "stress_gas"),
                scada_tight_hours=self._parse_int(self.scada_tight.get(), "scada_tight"),
                scada_relaxed_hours=self._parse_int(self.scada_relaxed.get(), "scada_relaxed"),
                scada_ramp_tight_per_hour=self._parse_float(self.scada_ramp_tight.get(), "scada_ramp_tight"),
                scada_ramp_relaxed_per_hour=self._parse_float(self.scada_ramp_relaxed.get(), "scada_ramp_relaxed"),
                import_zero_hours=self._parse_int(self.import_zero.get(), "import_zero"),
                import_half_hours=self._parse_int(self.import_half.get(), "import_half"),
                import_half_factor=self._parse_float(self.import_factor.get(), "import_factor"),
            ),
            reference_baseline_net=self.reference_baseline.get().strip() or None,
            working_yaml=self.working_yaml.get("1.0", tk.END).strip(),
        )

    def apply_controls_to_yaml(self) -> None:
        try:
            cfg = build_working_config(
                inputs=self._collect_inputs(),
                template_path=self.template_path,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.working_yaml.delete("1.0", tk.END)
        self.working_yaml.insert("1.0", dump_yaml(cfg))
        self.status.set("Working YAML updated.")
        self._save_state()

    def apply_yaml_to_controls(self) -> None:
        text = self.working_yaml.get("1.0", tk.END)
        try:
            cfg = yaml.safe_load(text)
            if not isinstance(cfg, dict):
                raise ValueError("YAML root must be mapping.")
        except Exception as exc:
            messagebox.showerror("Error", f"{tr(self.lang.get(), 'err_invalid_yaml')}\n{exc}")
            return
        if isinstance(cfg.get("run"), dict):
            rn = str(cfg["run"].get("name", "")).strip()
            if rn:
                self.scenario_slug.set(rn)
        if isinstance(cfg.get("countries"), list):
            self.countries.set(",".join(str(x) for x in cfg["countries"]))
        snaps = cfg.get("snapshots", {}) if isinstance(cfg.get("snapshots"), dict) else {}
        self.snapshot_start.set(str(snaps.get("start", self.snapshot_start.get())))
        self.snapshot_end.set(str(snaps.get("end", self.snapshot_end.get())))
        scenario = cfg.get("scenario", {}) if isinstance(cfg.get("scenario"), dict) else {}
        clusters = scenario.get("clusters", [])
        if isinstance(clusters, list) and clusters:
            self.clusters.set(str(clusters[0]))
        solving = cfg.get("solving", {}) if isinstance(cfg.get("solving"), dict) else {}
        solver = solving.get("solver", {}) if isinstance(solving.get("solver"), dict) else {}
        self.solver_name.set(str(solver.get("name", self.solver_name.get())))
        self.solver_options.set(str(solver.get("options", self.solver_options.get())))
        stress = cfg.get("stress_test", {}) if isinstance(cfg.get("stress_test"), dict) else {}
        self.stress_enable.set(bool(stress.get("enable", self.stress_enable.get())))
        self.country.set(str(stress.get("country", self.country.get())).upper())
        self.stress_load.set(str(stress.get("load_factor_full_window", self.stress_load.get())))
        self.stress_hydro.set(str(stress.get("hydro_factor_full_window", self.stress_hydro.get())))
        self.stress_gas.set(str(stress.get("gas_factor_first_72h", self.stress_gas.get())))
        scada = stress.get("scada", {}) if isinstance(stress.get("scada"), dict) else {}
        self.scada_tight.set(str(scada.get("tight_hours", self.scada_tight.get())))
        self.scada_relaxed.set(str(scada.get("relaxed_hours", self.scada_relaxed.get())))
        self.scada_ramp_tight.set(str(scada.get("ramp_tight_per_hour", self.scada_ramp_tight.get())))
        self.scada_ramp_relaxed.set(str(scada.get("ramp_relaxed_per_hour", self.scada_ramp_relaxed.get())))
        imp = stress.get("import_cap", {}) if isinstance(stress.get("import_cap"), dict) else {}
        self.import_zero.set(str(imp.get("zero_hours", self.import_zero.get())))
        self.import_half.set(str(imp.get("half_hours", self.import_half.get())))
        self.import_factor.set(str(imp.get("half_factor", self.import_factor.get())))
        self._update_mode_widgets()
        self._save_state()

    def refresh_baseline_networks(self) -> None:
        options = [str(path) for path in list_reference_baselines(self.repo_root)]
        self.reference_combo["values"] = options
        if self.reference_baseline.get() not in options:
            self.reference_baseline.set(options[0] if options else "")

    def _update_mode_widgets(self) -> None:
        self.reference_combo.configure(state="readonly" if self.run_mode.get() == "single" else "disabled")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def enqueue_job(self) -> None:
        try:
            inputs = self._collect_inputs()
            result = build_configs(
                self.repo_root,
                inputs=inputs,
                template_path=self.template_path,
            )
            commands = build_commands(inputs=inputs, build_result=result)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.status.set(str(exc))
            return

        job_id = uuid.uuid4().hex[:12]
        spec = JobSpec(
            job_id=job_id,
            output_name=inputs.output_name,
            mode=inputs.run_mode,  # type: ignore[arg-type]
            created_at=self._now_iso(),
            commands=[
                CommandSpec(
                    argv=list(c.argv),
                    description=c.description,
                    allow_failure=bool(c.allow_failure),
                )
                for c in commands
            ],
            generated_configs=[str(path) for path in result.generated_configs.values()],
            report_outdir=str(result.report_outdir),
            log_path=str(self.logs_dir / f"{job_id}.log"),
            scenario_run_name=result.scenario_run_name,
            baseline_run_name=result.baseline_run_name,
            country=inputs.country,
        )
        self.run_manager.enqueue(spec)
        self._jobs_dirty = True
        self.main_tabs.select(self.tab_runs)
        self.status.set(tr(self.lang.get(), "ok_job_queued"))
        self._save_state()

    def _mark_jobs_dirty(self) -> None:
        self._jobs_dirty = True

    def refresh_jobs_now(self) -> None:
        self._jobs_dirty = True
        self._poll_jobs()

    def _poll_jobs(self) -> None:
        jobs = self.run_manager.get_jobs()
        if self._jobs_dirty:
            self._job_by_id = {job.spec.job_id: job for job in jobs}
            selected = self._selected_job_id()
            self.tree_jobs.delete(*self.tree_jobs.get_children())
            for job in jobs:
                self.tree_jobs.insert(
                    "",
                    tk.END,
                    iid=job.spec.job_id,
                    values=(job.spec.job_id, job.status, job.spec.mode, job.spec.output_name, job.progress_message),
                )
            if selected and selected in self._job_by_id:
                self.tree_jobs.selection_set(selected)
            self.on_job_selected()
            self._jobs_dirty = False
            self._save_state()

        if any(job.status == "running" for job in jobs):
            self.spinner.start(12)
            self.spinner_label.configure(text=tr(self.lang.get(), "spinner_running"))
        else:
            self.spinner.stop()
            self.spinner_label.configure(text=tr(self.lang.get(), "spinner_idle"))

        self.root.after(self.JOB_POLL_MS, self._poll_jobs)

    def _selected_job_id(self) -> str | None:
        selected = self.tree_jobs.selection()
        return str(selected[0]) if selected else None

    def on_job_selected(self) -> None:
        job_id = self._selected_job_id()
        self.job_details.configure(state="normal")
        self.job_details.delete("1.0", tk.END)
        if not job_id or job_id not in self._job_by_id:
            self.job_details.configure(state="disabled")
            return
        job = self._job_by_id[job_id]
        lines = [
            f"Job: {job.spec.job_id}",
            f"Status: {job.status}",
            f"Mode: {job.spec.mode}",
            f"Output: {job.spec.output_name}",
            f"Created: {job.spec.created_at}",
            f"Started: {job.started_at or '-'}",
            f"Finished: {job.finished_at or '-'}",
            f"Exit: {job.exit_code if job.exit_code is not None else '-'}",
            f"Log: {job.spec.log_path}",
            "",
            "Commands:",
        ]
        lines.extend([f"- {' '.join(cmd.argv)}" for cmd in job.spec.commands])
        if job.error_summary:
            lines.extend(["", f"Error: {job.error_summary}"])
        self.job_details.insert("1.0", "\n".join(lines))
        self.job_details.configure(state="disabled")

    def cancel_selected_job(self) -> None:
        job_id = self._selected_job_id()
        if not job_id:
            return
        if self.run_manager.cancel(job_id):
            self._jobs_dirty = True
            self.status.set(f"Cancellation requested for {job_id}")
        else:
            self.status.set(f"Cannot cancel {job_id}")

    def refresh_results(self, *, force: bool = False) -> None:
        entries = scan_new_format_results(self.repo_root / "results")
        names = [entry.name for entry in entries]
        existing = [self.list_results.get(i) for i in range(self.list_results.size())]
        selected = self._selected_result_name() or self._saved_selected_result
        if force or names != existing:
            self.list_results.delete(0, tk.END)
            for name in names:
                self.list_results.insert(tk.END, name)
        self._result_by_name = {entry.name: entry.path for entry in entries}
        if selected in self._result_by_name:
            idx = names.index(selected)
            self.list_results.selection_clear(0, tk.END)
            self.list_results.selection_set(idx)
        elif names:
            self.list_results.selection_clear(0, tk.END)
            self.list_results.selection_set(0)
        self.on_result_selected()

    def _poll_results(self) -> None:
        self.refresh_results()
        self.root.after(self.RESULTS_POLL_MS, self._poll_results)

    def _selected_result_name(self) -> str | None:
        selected = self.list_results.curselection()
        return str(self.list_results.get(selected[0])) if selected else None

    def on_result_selected(self) -> None:
        name = self._selected_result_name()
        if not name or name not in self._result_by_name:
            self._set_text(self.summary_text, tr(self.lang.get(), "no_results"))
            self._set_text(self.assume_text, "")
            self.combo_csv["values"] = []
            self.list_fig.delete(0, tk.END)
            return
        folder = self._result_by_name[name]
        summary = parse_summary(folder)
        lines = [f"Result folder: {folder}"] + [f"{k}: {v}" for k, v in summary.items()]
        self._set_text(self.summary_text, "\n".join(lines))
        csv_files = sorted(path.name for path in folder.glob("*.csv"))
        self.combo_csv["values"] = csv_files
        if csv_files:
            if self.combo_csv.get() not in csv_files:
                self.combo_csv.set(csv_files[0])
            self.on_csv_selected()
        self.list_fig.delete(0, tk.END)
        for fig in sorted(path.name for path in folder.glob("*.png")):
            self.list_fig.insert(tk.END, fig)
        if self.list_fig.size() > 0:
            self.list_fig.selection_set(0)
            self.on_figure_selected()
        assume = folder / "assumptions_limitations.md"
        self._set_text(self.assume_text, assume.read_text(encoding="utf-8") if assume.exists() else "")
        self._save_state()

    def on_csv_selected(self) -> None:
        result_name = self._selected_result_name()
        csv_name = self.combo_csv.get()
        if not result_name or not csv_name:
            return
        folder = self._result_by_name.get(result_name)
        if folder is None:
            return
        df = load_csv_preview(folder / csv_name, max_rows=200)
        self._fill_tree(self.tree_csv, df)

    def on_figure_selected(self) -> None:
        result_name = self._selected_result_name()
        if not result_name:
            return
        folder = self._result_by_name.get(result_name)
        if folder is None:
            return
        selected = self.list_fig.curselection()
        if not selected:
            return
        fig = folder / str(self.list_fig.get(selected[0]))
        try:
            self._result_image = tk.PhotoImage(file=str(fig))
            self.fig_label.configure(image=self._result_image, text="")
        except tk.TclError:
            self._result_image = None
            self.fig_label.configure(image="", text=f"Cannot preview image:\n{fig}")

    def _fill_tree(self, tree: ttk.Treeview, df: Any) -> None:
        tree.delete(*tree.get_children())
        cols = [str(c) for c in df.columns]
        tree["columns"] = cols
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="w")
        for row in df.itertuples(index=False):
            tree.insert("", tk.END, values=[str(v) for v in row])

    def _set_text(self, widget: scrolledtext.ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _ui_state(self) -> dict[str, Any]:
        tab_name = {str(self.tab_builder): "builder", str(self.tab_runs): "runs", str(self.tab_results): "results"}
        current_tab = tab_name.get(str(self.main_tabs.select()), "builder")
        return {
            "language": self.lang.get(),
            "main_tab": current_tab,
            "run_mode": self.run_mode.get(),
            "output_name": self.output_name.get(),
            "scenario_slug": self.scenario_slug.get(),
            "country": self.country.get(),
            "countries": self.countries.get(),
            "snapshot_start": self.snapshot_start.get(),
            "snapshot_end": self.snapshot_end.get(),
            "clusters": self.clusters.get(),
            "solver_name": self.solver_name.get(),
            "solver_options": self.solver_options.get(),
            "reference_baseline_net": self.reference_baseline.get(),
            "stress_enable": bool(self.stress_enable.get()),
            "stress_load_factor": self.stress_load.get(),
            "stress_hydro_factor": self.stress_hydro.get(),
            "stress_gas_factor": self.stress_gas.get(),
            "scada_tight_hours": self.scada_tight.get(),
            "scada_relaxed_hours": self.scada_relaxed.get(),
            "scada_ramp_tight": self.scada_ramp_tight.get(),
            "scada_ramp_relaxed": self.scada_ramp_relaxed.get(),
            "import_zero_hours": self.import_zero.get(),
            "import_half_hours": self.import_half.get(),
            "import_half_factor": self.import_factor.get(),
            "working_yaml": self.working_yaml.get("1.0", tk.END),
            "selected_result": self._selected_result_name() or "",
        }

    def _save_state(self) -> None:
        try:
            save_state(
                self.state_path,
                language=self.lang.get(),
                jobs=self.run_manager.get_jobs(),
                ui_state=self._ui_state(),
            )
        except OSError:
            pass

    def on_close(self) -> None:
        self._save_state()
        self.run_manager.shutdown()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    ScenarioManagerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
