from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "1_piele_dashboard"))

from scenario_manager import config_builder
from scenario_manager.config_builder import build_commands, build_configs
from scenario_manager.results_index import REQUIRED_CSVS, scan_new_format_results
from scenario_manager.run_manager import RunManager
from scenario_manager.state_store import load_state
from scenario_manager.types import (
    CommandSpec,
    ConfigBuildResult,
    JobSpec,
    ScenarioInputs,
    StressParams,
)


def _inputs(run_mode: str = "paired", baseline: str | None = None) -> ScenarioInputs:
    return ScenarioInputs(
        run_mode=run_mode,  # type: ignore[arg-type]
        output_name="test-output",
        scenario_slug="test-slug",
        country="RO",
        countries=["RO", "BG", "HU", "RS"],
        snapshot_start="2020-12-01",
        snapshot_end="2020-12-08",
        clusters=10,
        solver_name="highs",
        solver_options="highs-simplex",
        stress_enable=True,
        stress=StressParams(),
        reference_baseline_net=baseline,
    )


def test_build_configs_template_immutable_and_paired(tmp_path: Path) -> None:
    template_src = ROOT / "1_piele_docs" / "scenario_template.yaml"
    template_path = tmp_path / "1_piele_docs" / "scenario_template.yaml"
    template_path.parent.mkdir(parents=True)
    template_path.write_text(template_src.read_text(encoding="utf-8"), encoding="utf-8")
    before = template_path.read_text(encoding="utf-8")

    (tmp_path / "results").mkdir()
    result = build_configs(tmp_path, inputs=_inputs(), template_path=template_path)

    assert "scenario" in result.generated_configs
    assert "baseline" in result.generated_configs
    assert not result.scenario_network_target.is_absolute()
    assert not result.baseline_network_target.is_absolute()
    baseline_cfg = yaml.safe_load(result.generated_configs["baseline"].read_text(encoding="utf-8"))
    assert baseline_cfg["stress_test"]["enable"] is False
    assert template_path.read_text(encoding="utf-8") == before


def test_build_configs_single_requires_reference_baseline(tmp_path: Path) -> None:
    template_src = ROOT / "1_piele_docs" / "scenario_template.yaml"
    template_path = tmp_path / "1_piele_docs" / "scenario_template.yaml"
    template_path.parent.mkdir(parents=True)
    template_path.write_text(template_src.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "results").mkdir()

    with pytest.raises(ValueError):
        build_configs(tmp_path, inputs=_inputs(run_mode="single"), template_path=template_path)

    with pytest.raises(ValueError):
        build_configs(
            tmp_path,
            inputs=_inputs(run_mode="single", baseline=str(tmp_path / "missing.nc")),
            template_path=template_path,
        )


def test_scan_new_format_results_filters_only_complete_folders(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    valid = results_dir / "valid"
    invalid = results_dir / "invalid"
    valid.mkdir(parents=True)
    invalid.mkdir(parents=True)

    for name in REQUIRED_CSVS:
        (valid / name).write_text("col\n1\n", encoding="utf-8")

    for name in REQUIRED_CSVS[:-1]:
        (invalid / name).write_text("col\n1\n", encoding="utf-8")

    entries = scan_new_format_results(results_dir)
    assert [entry.name for entry in entries] == ["valid"]


def test_load_state_marks_running_jobs_as_interrupted(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "language": "en",
        "ui_state": {},
        "jobs": [
            {
                "spec": {
                    "job_id": "abc123",
                    "output_name": "x",
                    "mode": "paired",
                    "created_at": now,
                    "commands": [{"argv": ["python", "-c", "print(1)"], "description": "test"}],
                    "generated_configs": [],
                    "report_outdir": "results/x",
                    "log_path": "logs/x.log",
                    "scenario_run_name": "scenario-x",
                    "baseline_run_name": "baseline-x",
                    "country": "RO",
                },
                "status": "running",
                "started_at": now,
            }
        ],
    }
    state_file.write_text(json.dumps(payload), encoding="utf-8")
    state = load_state(state_file)
    assert state["jobs"][0].status == "interrupted"


def test_run_manager_queue_and_failed_job(tmp_path: Path) -> None:
    manager = RunManager(repo_root=tmp_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        job1 = JobSpec(
            job_id="job1",
            output_name="r1",
            mode="paired",
            created_at=now,
            commands=[
                CommandSpec(
                    argv=[sys.executable, "-c", "import time; time.sleep(1.2); print('ok')"],
                    description="sleep",
                )
            ],
            generated_configs=[],
            report_outdir="results/r1",
            log_path=str(tmp_path / "job1.log"),
            scenario_run_name="s1",
            baseline_run_name="b1",
            country="RO",
        )
        job2 = JobSpec(
            job_id="job2",
            output_name="r2",
            mode="single",
            created_at=now,
            commands=[
                CommandSpec(
                    argv=[sys.executable, "-c", "import sys; sys.exit(3)"],
                    description="fail",
                )
            ],
            generated_configs=[],
            report_outdir="results/r2",
            log_path=str(tmp_path / "job2.log"),
            scenario_run_name="s2",
            baseline_run_name=None,
            country="RO",
        )
        manager.enqueue(job1)
        manager.enqueue(job2)

        found_running_and_queued = False
        t0 = time.time()
        while time.time() - t0 < 5:
            jobs = {job.spec.job_id: job for job in manager.get_jobs()}
            if jobs["job1"].status == "running" and jobs["job2"].status == "queued":
                found_running_and_queued = True
                break
            time.sleep(0.1)
        assert found_running_and_queued

        t1 = time.time()
        while time.time() - t1 < 20:
            jobs = {job.spec.job_id: job for job in manager.get_jobs()}
            if jobs["job1"].status in {"succeeded", "failed"} and jobs["job2"].status in {
                "failed",
                "succeeded",
                "cancelled",
            }:
                break
            time.sleep(0.2)

        jobs = {job.spec.job_id: job for job in manager.get_jobs()}
        assert jobs["job1"].status == "succeeded"
        assert jobs["job2"].status == "failed"
        assert jobs["job2"].exit_code == 3
    finally:
        manager.shutdown()


def test_build_commands_conda_fallback_when_snakemake_module_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config_builder, "_has_module", lambda _: False)
    monkeypatch.setattr(config_builder, "_find_conda_executable", lambda: "conda")
    monkeypatch.setattr(config_builder, "_select_conda_prefix", lambda: None)
    monkeypatch.setenv("PLANUI_CONDA_ENV", "pypsa")

    result = ConfigBuildResult(
        generated_configs={
            "scenario": tmp_path / "scenario.yaml",
            "baseline": tmp_path / "baseline.yaml",
        },
        scenario_run_name="scenario-x",
        baseline_run_name="baseline-x",
        scenario_network_target=tmp_path / "results" / "scenario-x" / "networks" / "base_s_10_elec_.nc",
        baseline_network_target=tmp_path / "results" / "baseline-x" / "networks" / "base_s_10_elec_.nc",
        report_outdir=tmp_path / "results" / "comparison-x",
        scenario_config={},
        baseline_config={},
    )

    commands = build_commands(inputs=_inputs(), build_result=result)
    assert commands
    assert commands[0].argv[:7] == ["conda", "run", "-n", "pypsa", "python", "-m", "snakemake"]
    assert commands[-1].argv[:5] == ["conda", "run", "-n", "pypsa", "python"]


def test_build_commands_prefers_conda_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config_builder, "_has_module", lambda _: False)
    monkeypatch.setattr(config_builder, "_find_conda_executable", lambda: "conda")
    monkeypatch.setattr(
        config_builder,
        "_select_conda_prefix",
        lambda: r"C:\Users\Administrator\.conda\envs\pypsa-eur",
    )

    result = ConfigBuildResult(
        generated_configs={
            "scenario": tmp_path / "scenario.yaml",
            "baseline": tmp_path / "baseline.yaml",
        },
        scenario_run_name="scenario-x",
        baseline_run_name="baseline-x",
        scenario_network_target=tmp_path / "results" / "scenario-x" / "networks" / "base_s_10_elec_.nc",
        baseline_network_target=tmp_path / "results" / "baseline-x" / "networks" / "base_s_10_elec_.nc",
        report_outdir=tmp_path / "results" / "comparison-x",
        scenario_config={},
        baseline_config={},
    )

    commands = build_commands(inputs=_inputs(), build_result=result)
    assert commands
    assert commands[0].argv[:8] == [
        "conda",
        "run",
        "-p",
        r"C:\Users\Administrator\.conda\envs\pypsa-eur",
        "python",
        "-m",
        "snakemake",
        "--unlock",
    ]
