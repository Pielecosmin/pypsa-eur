from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scenario_manager.types import CommandSpec, ConfigBuildResult, ScenarioInputs

GENERATED_CONFIG_DIR = Path("config/adversarial/generated")
DEFAULT_CONDA_PREFIX = Path(r"C:\Users\Administrator\.conda\envs\pypsa-eur")


def sanitize_slug(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "scenario"


def load_template(template_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Template at {template_path} must be a YAML mapping.")
    return raw


def resolve_template_path(base_template_path: Path, cutout_year: str = "2020") -> Path:
    """Resolve template path based on cutout year.
    
    Intelligently selects year-specific templates:
    - If cutout_year = "2023", looks for scenario_template_2023.yaml
    - If cutout_year = "2020", uses default scenario_template.yaml
    - Falls back to base template if year-specific not found
    
    Args:
        base_template_path: Path to default template (e.g., scenario_template.yaml)
        cutout_year: Year as string ("2020" or "2023")
    
    Returns:
        Path to the template file to use
    """
    if cutout_year not in ("2020", "2023"):
        return base_template_path
    
    # 2020 uses default template
    if cutout_year == "2020":
        return base_template_path
    
    # 2023 looks for year-specific template
    if cutout_year == "2023":
        year_specific = base_template_path.parent / "scenario_template_2023.yaml"
        if year_specific.exists():
            return year_specific
    
    # Fallback to default if year-specific not found
    return base_template_path


def dump_yaml(config: dict[str, Any]) -> str:
    return yaml.safe_dump(config, sort_keys=False)


def parse_working_yaml(yaml_text: str) -> dict[str, Any]:
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError("Working YAML must parse to a mapping.")
    return raw


def list_reference_baselines(repo_root: Path) -> list[Path]:
    results_dir = repo_root / "results"
    if not results_dir.exists():
        return []
    items = sorted(results_dir.glob("*/networks/base_s_*_elec_.nc"))
    return [p.resolve() for p in items]


def _ensure_mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if isinstance(value, dict):
        return value
    parent[key] = {}
    return parent[key]


def _apply_inputs_to_config(
    base_cfg: dict[str, Any],
    *,
    inputs: ScenarioInputs,
    run_name: str,
    stress_enabled: bool,
) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)

    run_cfg = _ensure_mapping(cfg, "run")
    run_cfg["name"] = run_name
    run_cfg.setdefault("disable_progressbar", True)
    run_cfg.setdefault("shared_resources", {"policy": False})

    scenario_cfg = _ensure_mapping(cfg, "scenario")
    scenario_cfg["clusters"] = [int(inputs.clusters)]
    scenario_cfg.setdefault("opts", [""])

    cfg["countries"] = list(inputs.countries)

    snapshots = _ensure_mapping(cfg, "snapshots")
    snapshots["start"] = inputs.snapshot_start
    snapshots["end"] = inputs.snapshot_end

    solving = _ensure_mapping(cfg, "solving")
    solver_cfg = _ensure_mapping(solving, "solver")
    solver_cfg["name"] = inputs.solver_name
    solver_cfg["options"] = inputs.solver_options

    stress_cfg = _ensure_mapping(cfg, "stress_test")
    stress_cfg["enable"] = bool(stress_enabled)
    stress_cfg["country"] = inputs.country
    stress_cfg["load_factor_full_window"] = float(inputs.stress.load_factor_full_window)
    stress_cfg["hydro_factor_full_window"] = float(inputs.stress.hydro_factor_full_window)
    stress_cfg["gas_factor_first_72h"] = float(inputs.stress.gas_factor_first_72h)
    stress_cfg["scada"] = {
        "tight_hours": int(inputs.stress.scada_tight_hours),
        "relaxed_hours": int(inputs.stress.scada_relaxed_hours),
        "ramp_tight_per_hour": float(inputs.stress.scada_ramp_tight_per_hour),
        "ramp_relaxed_per_hour": float(inputs.stress.scada_ramp_relaxed_per_hour),
    }
    stress_cfg["import_cap"] = {
        "zero_hours": int(inputs.stress.import_zero_hours),
        "half_hours": int(inputs.stress.import_half_hours),
        "half_factor": float(inputs.stress.import_half_factor),
    }

    return cfg


def _base_config_from_inputs(
    template_config: dict[str, Any],
    working_yaml: str | None,
) -> dict[str, Any]:
    if working_yaml and working_yaml.strip():
        return parse_working_yaml(working_yaml)
    return copy.deepcopy(template_config)


def _apply_cutout_to_config(cfg: dict[str, Any], cutout_year: str) -> None:
    """Apply cutout year selection to configuration.
    
    Sets the default_cutout in atlite section and updates electricity year.
    Also validates that snapshot dates match the selected year.
    
    Args:
        cfg: Configuration dictionary to modify in-place
        cutout_year: Year as string ("2020" or "2023")
    
    Raises:
        ValueError: If cutout_year is invalid or dates don't match year
    """
    if cutout_year not in ("2020", "2023"):
        raise ValueError(f"Unsupported cutout year: {cutout_year}. Must be 2020 or 2023.")
    
    # Determine cutout name
    cutout_name = f"europe-{cutout_year}-sarah3-era5"
    
    # Validate atlite config has both cutout definitions
    if "atlite" not in cfg:
        cfg["atlite"] = {}
    
    atlite_cfg = cfg["atlite"]
    if "cutouts" not in atlite_cfg:
        atlite_cfg["cutouts"] = {}
    
    if cutout_name not in atlite_cfg["cutouts"]:
        raise ValueError(
            f"Cutout {cutout_name} not defined in template. "
            "Make sure scenario template has both 2020 and 2023 cutout definitions."
        )
    
    # Set default cutout
    atlite_cfg["default_cutout"] = cutout_name
    
    # Update electricity year to match cutout year
    electricity_cfg = cfg.get("electricity", {})
    if "estimate_renewable_capacities" in electricity_cfg:
        electricity_cfg["estimate_renewable_capacities"]["year"] = int(cutout_year)
    
    # Validate snapshot dates match the year and are in correct order
    if "snapshots" in cfg:
        snapshots = cfg["snapshots"]
        if isinstance(snapshots, dict) and "start" in snapshots and "end" in snapshots:
            snap_start_str = str(snapshots["start"])
            snap_end_str = str(snapshots["end"])
            
            # Extract year from date string (format: YYYY-MM-DD)
            start_year = snap_start_str.split("-")[0] if "-" in snap_start_str else snap_start_str[:4]
            end_year = snap_end_str.split("-")[0] if "-" in snap_end_str else snap_end_str[:4]
            
            # Check year matching
            if start_year != cutout_year or end_year != cutout_year:
                raise ValueError(
                    f"Snapshot dates don't match cutout year {cutout_year}: "
                    f"got {snap_start_str} to {snap_end_str}. "
                    "Cutout year must match snapshot year."
                )
            
            # Check date order (start <= end)
            try:
                from datetime import datetime
                start_date = datetime.strptime(snap_start_str, "%Y-%m-%d")
                end_date = datetime.strptime(snap_end_str, "%Y-%m-%d")
                if start_date > end_date:
                    raise ValueError(
                        f"Invalid snapshot range: start date ({snap_start_str}) "
                        f"is after end date ({snap_end_str}). "
                        "Start date must be before or equal to end date."
                    )
            except ValueError as e:
                # Re-raise if it's our custom error, otherwise just pass (format already validated)
                if "Invalid snapshot range" in str(e):
                    raise



def _network_target(run_name: str, clusters: int) -> Path:
    return Path("results") / run_name / "networks" / f"base_s_{clusters}_elec_.nc"


def _snake_target_str(path: Path) -> str:
    return path.as_posix()


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _find_conda_executable() -> str | None:
    candidates: list[str] = []

    conda_env_var = os.environ.get("CONDA_EXE")
    if conda_env_var:
        candidates.append(conda_env_var)

    py_dir = Path(sys.executable).resolve().parent
    candidates.extend(
        [
            str(py_dir / "conda.exe"),
            str(py_dir / "Scripts" / "conda.exe"),
        ]
    )

    which_conda = shutil.which("conda")
    if which_conda:
        candidates.append(which_conda)

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return str(path)
    return None


def _list_conda_env_names(conda_exe: str) -> set[str]:
    try:
        completed = subprocess.run(
            [conda_exe, "env", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return set()

    env_paths = payload.get("envs", [])
    names: set[str] = set()
    for entry in env_paths:
        path = Path(str(entry))
        names.add(path.name)
    return names


def _select_conda_env_name(conda_exe: str) -> str:
    explicit = os.environ.get("PLANUI_CONDA_ENV")
    if explicit:
        return explicit

    candidates: list[str] = []
    current = os.environ.get("CONDA_DEFAULT_ENV")
    if current and current != "base":
        candidates.append(current)
    candidates.extend(["pypsa", "pypsa-eur"])

    available = _list_conda_env_names(conda_exe)
    if available:
        for name in candidates:
            if name in available:
                return name
    return candidates[0]


def _select_conda_prefix() -> str | None:
    explicit = os.environ.get("PLANUI_CONDA_PREFIX")
    if explicit:
        path = Path(explicit)
        if path.exists():
            return str(path)
        return None

    if DEFAULT_CONDA_PREFIX.exists():
        return str(DEFAULT_CONDA_PREFIX)
    return None


def resolve_runtime_prefixes() -> tuple[list[str], list[str], str]:
    """Resolve execution prefixes for snakemake and python commands.

    Priority:
    1. Preferred conda prefix (`conda run -p ...`) when available.
    2. Current interpreter if it has snakemake.
    3. Conda fallback (`conda run -n ...`) when available.
    4. PATH snakemake executable fallback.
    """
    conda_exe = _find_conda_executable()
    conda_prefix = _select_conda_prefix()
    if conda_exe and conda_prefix:
        return (
            [conda_exe, "run", "-p", conda_prefix, "python", "-m", "snakemake"],
            [conda_exe, "run", "-p", conda_prefix, "python"],
            "conda-run-prefix",
        )

    if _has_module("snakemake"):
        return [sys.executable, "-m", "snakemake"], [sys.executable], "active-python"

    if conda_exe:
        env_name = _select_conda_env_name(conda_exe)
        return (
            [conda_exe, "run", "-n", env_name, "python", "-m", "snakemake"],
            [conda_exe, "run", "-n", env_name, "python"],
            "conda-run",
        )

    snakemake_exe = shutil.which("snakemake")
    if snakemake_exe:
        snakemake_path = Path(snakemake_exe)
        candidate_python = snakemake_path.parent / "python.exe"
        python_prefix = [str(candidate_python)] if candidate_python.exists() else [sys.executable]
        return [snakemake_exe], python_prefix, "path-snakemake"

    return [sys.executable, "-m", "snakemake"], [sys.executable], "active-python"


def _snakemake_extra_args() -> list[str]:
    # Default to skipping cached-http remote metadata checks to avoid proxy
    # authentication failures during DAG build in locked-down environments.
    raw = os.environ.get("PLANUI_SNAKEMAKE_SKIP_REMOTE_CHECKS", "1").strip().lower()
    if raw in {"0", "false", "no"}:
        return []
    return ["--storage-cached-http-skip-remote-checks"]


def build_working_config(
    *,
    inputs: ScenarioInputs,
    template_path: Path,
) -> dict[str, Any]:
    # Intelligently select template based on cutout_year
    resolved_template_path = resolve_template_path(template_path, inputs.cutout_year)
    template_cfg = load_template(resolved_template_path)
    working_base = _base_config_from_inputs(template_cfg, inputs.working_yaml)
    run_name = sanitize_slug(inputs.scenario_slug or "working-draft")
    return _apply_inputs_to_config(
        working_base,
        inputs=inputs,
        run_name=run_name,
        stress_enabled=bool(inputs.stress_enable),
    )


def build_configs(
    repo_root: Path,
    *,
    inputs: ScenarioInputs,
    template_path: Path,
) -> ConfigBuildResult:
    if not inputs.output_name.strip():
        raise ValueError("Output name is required.")

    report_outdir = repo_root / "results" / inputs.output_name
    if report_outdir.exists():
        raise ValueError("Result output folder already exists.")

    if inputs.run_mode == "single":
        if not inputs.reference_baseline_net:
            raise ValueError("Single mode requires a reference baseline network.")
        baseline_net = Path(inputs.reference_baseline_net)
        if not baseline_net.exists():
            raise ValueError("Reference baseline network does not exist.")

    # Intelligently select template based on cutout_year
    resolved_template_path = resolve_template_path(template_path, inputs.cutout_year)
    template_cfg = load_template(resolved_template_path)
    working_base = _base_config_from_inputs(template_cfg, inputs.working_yaml)

    now_token = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = sanitize_slug(inputs.scenario_slug or inputs.output_name)

    scenario_run_name = f"{slug}-scenario-{now_token}"
    baseline_run_name: str | None = (
        f"{slug}-baseline-{now_token}" if inputs.run_mode == "paired" else None
    )

    scenario_cfg = _apply_inputs_to_config(
        working_base,
        inputs=inputs,
        run_name=scenario_run_name,
        stress_enabled=bool(inputs.stress_enable),
    )
    _apply_cutout_to_config(scenario_cfg, inputs.cutout_year)

    baseline_cfg: dict[str, Any] | None = None
    if inputs.run_mode == "paired":
        baseline_cfg = _apply_inputs_to_config(
            working_base,
            inputs=inputs,
            run_name=baseline_run_name or "",
            stress_enabled=False,
        )
        _apply_cutout_to_config(baseline_cfg, inputs.cutout_year)

    cfg_dir = repo_root / GENERATED_CONFIG_DIR
    cfg_dir.mkdir(parents=True, exist_ok=True)

    scenario_cfg_path = cfg_dir / f"{slug}_{now_token}_scenario.yaml"
    scenario_cfg_path.write_text(dump_yaml(scenario_cfg), encoding="utf-8")

    generated = {"scenario": scenario_cfg_path}
    baseline_cfg_path: Path | None = None
    if baseline_cfg is not None:
        baseline_cfg_path = cfg_dir / f"{slug}_{now_token}_baseline.yaml"
        baseline_cfg_path.write_text(dump_yaml(baseline_cfg), encoding="utf-8")
        generated["baseline"] = baseline_cfg_path

    scenario_target = _network_target(scenario_run_name, inputs.clusters)
    baseline_target = _network_target(baseline_run_name or "", inputs.clusters) if baseline_run_name else None

    return ConfigBuildResult(
        generated_configs=generated,
        scenario_run_name=scenario_run_name,
        baseline_run_name=baseline_run_name,
        scenario_network_target=scenario_target,
        baseline_network_target=baseline_target,
        report_outdir=report_outdir,
        scenario_config=scenario_cfg,
        baseline_config=baseline_cfg,
    )


def build_commands(
    *,
    inputs: ScenarioInputs,
    build_result: ConfigBuildResult,
) -> list[CommandSpec]:
    snakemake_prefix, python_prefix, runtime_mode = resolve_runtime_prefixes()
    scenario_cfg = str(build_result.generated_configs["scenario"])
    scenario_target = _snake_target_str(build_result.scenario_network_target)
    report_outdir = str(build_result.report_outdir)

    commands: list[CommandSpec] = []
    extra = _snakemake_extra_args()

    if inputs.run_mode == "paired":
        baseline_cfg_path = build_result.generated_configs.get("baseline")
        if baseline_cfg_path is None or build_result.baseline_network_target is None:
            raise ValueError("Paired mode requires generated baseline config and target.")
        baseline_cfg = str(baseline_cfg_path)
        baseline_target = _snake_target_str(build_result.baseline_network_target)

        commands.extend(
            [
                CommandSpec(
                    argv=[*snakemake_prefix, *extra, "--unlock", "--configfile", baseline_cfg],
                    description=f"Unlock baseline workflow [{runtime_mode}]",
                    allow_failure=True,
                ),
                CommandSpec(
                    argv=[
                        *snakemake_prefix,
                        *extra,
                        "-c",
                        "all",
                        baseline_target,
                        "--configfile",
                        baseline_cfg,
                    ],
                    description=f"Solve baseline scenario [{runtime_mode}]",
                ),
            ]
        )

        baseline_net = baseline_target
    else:
        baseline_net = str(Path(inputs.reference_baseline_net or ""))

    commands.extend(
        [
            CommandSpec(
                argv=[*snakemake_prefix, *extra, "--unlock", "--configfile", scenario_cfg],
                description=f"Unlock scenario workflow [{runtime_mode}]",
                allow_failure=True,
            ),
            CommandSpec(
                argv=[
                    *snakemake_prefix,
                    *extra,
                    "-c",
                    "all",
                    scenario_target,
                    "--configfile",
                    scenario_cfg,
                ],
                description=f"Solve scenario [{runtime_mode}]",
            ),
            CommandSpec(
                argv=[
                    *python_prefix,
                    "scripts/report_romania_winter_stress.py",
                    "--baseline-net",
                    baseline_net,
                    "--scenario-net",
                    scenario_target,
                    "--country",
                    inputs.country,
                    "--outdir",
                    report_outdir,
                ],
                description=f"Generate comparison report [{runtime_mode}]",
            ),
        ]
    )

    return commands
