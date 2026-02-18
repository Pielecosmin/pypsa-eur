from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scenario_manager.types import CommandSpec, JobRecord, JobSpec

DEFAULT_STATE: dict[str, Any] = {
    "language": "en",
    "jobs": [],
    "ui_state": {},
}


def _command_from_dict(data: dict[str, Any]) -> CommandSpec:
    return CommandSpec(
        argv=list(data.get("argv", [])),
        description=str(data.get("description", "")),
    )


def _spec_from_dict(data: dict[str, Any]) -> JobSpec:
    return JobSpec(
        job_id=str(data.get("job_id", "")),
        output_name=str(data.get("output_name", "")),
        mode=str(data.get("mode", "paired")),  # type: ignore[arg-type]
        created_at=str(data.get("created_at", "")),
        commands=[_command_from_dict(c) for c in data.get("commands", [])],
        generated_configs=[str(p) for p in data.get("generated_configs", [])],
        report_outdir=str(data.get("report_outdir", "")),
        log_path=str(data.get("log_path", "")),
        scenario_run_name=str(data.get("scenario_run_name", "")),
        baseline_run_name=(
            str(data.get("baseline_run_name"))
            if data.get("baseline_run_name") is not None
            else None
        ),
        country=str(data.get("country", "RO")),
    )


def _record_from_dict(data: dict[str, Any]) -> JobRecord:
    record = JobRecord(
        spec=_spec_from_dict(data.get("spec", {})),
        status=str(data.get("status", "queued")),  # type: ignore[arg-type]
        started_at=str(data.get("started_at")) if data.get("started_at") else None,
        finished_at=str(data.get("finished_at")) if data.get("finished_at") else None,
        exit_code=int(data["exit_code"]) if data.get("exit_code") is not None else None,
        error_summary=(
            str(data.get("error_summary")) if data.get("error_summary") else None
        ),
        progress_message=str(data.get("progress_message", "")),
        cancel_requested=bool(data.get("cancel_requested", False)),
    )
    if record.status == "running":
        record.status = "interrupted"
        record.progress_message = "Interrupted by app restart."
        record.cancel_requested = False
        if record.finished_at is None:
            record.finished_at = record.started_at or record.spec.created_at
    return record


def job_record_to_dict(record: JobRecord) -> dict[str, Any]:
    return asdict(record)


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)

    state = dict(DEFAULT_STATE)
    state["language"] = str(data.get("language", DEFAULT_STATE["language"]))
    state["ui_state"] = dict(data.get("ui_state", {}))
    state["jobs"] = [_record_from_dict(item) for item in data.get("jobs", [])]
    return state


def save_state(
    state_path: Path,
    *,
    language: str,
    jobs: list[JobRecord],
    ui_state: dict[str, Any],
) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "language": language,
        "ui_state": ui_state,
        "jobs": [job_record_to_dict(record) for record in jobs],
    }
    state_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
