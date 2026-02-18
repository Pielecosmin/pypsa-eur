from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

JobStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    "interrupted",
]


@dataclass
class StressParams:
    load_factor_full_window: float = 1.12
    hydro_factor_full_window: float = 0.60
    gas_factor_first_72h: float = 0.70
    scada_tight_hours: int = 24
    scada_relaxed_hours: int = 48
    scada_ramp_tight_per_hour: float = 0.10
    scada_ramp_relaxed_per_hour: float = 0.25
    import_zero_hours: int = 48
    import_half_hours: int = 48
    import_half_factor: float = 0.50


@dataclass
class ScenarioInputs:
    run_mode: Literal["paired", "single"]
    output_name: str
    scenario_slug: str
    country: str
    countries: list[str]
    snapshot_start: str
    snapshot_end: str
    clusters: int
    solver_name: str
    solver_options: str
    stress_enable: bool = True
    stress: StressParams = field(default_factory=StressParams)
    reference_baseline_net: str | None = None
    working_yaml: str | None = None


@dataclass
class CommandSpec:
    argv: list[str]
    description: str


@dataclass
class ConfigBuildResult:
    generated_configs: dict[str, Path]
    scenario_run_name: str
    baseline_run_name: str | None
    scenario_network_target: Path
    baseline_network_target: Path | None
    report_outdir: Path
    scenario_config: dict[str, Any]
    baseline_config: dict[str, Any] | None


@dataclass
class JobSpec:
    job_id: str
    output_name: str
    mode: Literal["paired", "single"]
    created_at: str
    commands: list[CommandSpec]
    generated_configs: list[str]
    report_outdir: str
    log_path: str
    scenario_run_name: str
    baseline_run_name: str | None
    country: str


@dataclass
class JobRecord:
    spec: JobSpec
    status: JobStatus = "queued"
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    error_summary: str | None = None
    progress_message: str = ""
    cancel_requested: bool = False


@dataclass
class ResultEntry:
    name: str
    path: Path
    timestamp: float
    required_files_present: bool
    csv_files: list[str]
    figure_files: list[str]
    assumptions_file: Path | None
