from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scenario_manager.types import CommandSpec, ConfigBuildResult, ScenarioInputs

GENERATED_CONFIG_DIR = Path("config/adversarial/generated")


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


def _network_target(run_name: str, clusters: int) -> Path:
    return Path("results") / run_name / "networks" / f"base_s_{clusters}_elec_.nc"


def build_working_config(
    *,
    inputs: ScenarioInputs,
    template_path: Path,
) -> dict[str, Any]:
    template_cfg = load_template(template_path)
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

    template_cfg = load_template(template_path)
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

    baseline_cfg: dict[str, Any] | None = None
    if inputs.run_mode == "paired":
        baseline_cfg = _apply_inputs_to_config(
            working_base,
            inputs=inputs,
            run_name=baseline_run_name or "",
            stress_enabled=False,
        )

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

    scenario_target = repo_root / _network_target(scenario_run_name, inputs.clusters)
    baseline_target = (
        repo_root / _network_target(baseline_run_name or "", inputs.clusters)
        if baseline_run_name
        else None
    )

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
    scenario_cfg = str(build_result.generated_configs["scenario"])
    scenario_target = str(build_result.scenario_network_target)
    report_outdir = str(build_result.report_outdir)

    commands: list[CommandSpec] = []

    if inputs.run_mode == "paired":
        baseline_cfg_path = build_result.generated_configs.get("baseline")
        if baseline_cfg_path is None or build_result.baseline_network_target is None:
            raise ValueError("Paired mode requires generated baseline config and target.")
        baseline_cfg = str(baseline_cfg_path)
        baseline_target = str(build_result.baseline_network_target)

        commands.extend(
            [
                CommandSpec(
                    argv=["snakemake", "--unlock", "--configfile", baseline_cfg],
                    description="Unlock baseline workflow",
                ),
                CommandSpec(
                    argv=[
                        "snakemake",
                        "-c",
                        "all",
                        baseline_target,
                        "--configfile",
                        baseline_cfg,
                    ],
                    description="Solve baseline scenario",
                ),
            ]
        )

        baseline_net = baseline_target
    else:
        baseline_net = str(Path(inputs.reference_baseline_net or ""))

    commands.extend(
        [
            CommandSpec(
                argv=["snakemake", "--unlock", "--configfile", scenario_cfg],
                description="Unlock scenario workflow",
            ),
            CommandSpec(
                argv=[
                    "snakemake",
                    "-c",
                    "all",
                    scenario_target,
                    "--configfile",
                    scenario_cfg,
                ],
                description="Solve scenario",
            ),
            CommandSpec(
                argv=[
                    "python",
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
                description="Generate comparison report",
            ),
        ]
    )

    return commands
