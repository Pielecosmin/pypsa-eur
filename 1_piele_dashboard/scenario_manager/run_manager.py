from __future__ import annotations

import copy
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from scenario_manager.types import JobRecord, JobSpec


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunManager:
    def __init__(
        self,
        *,
        repo_root: Path,
        jobs: list[JobRecord] | None = None,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self.repo_root = repo_root
        self._jobs = list(jobs or [])
        self._on_change = on_change

        self._lock = threading.RLock()
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._active_process: subprocess.Popen[str] | None = None
        self._active_job_id: str | None = None

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def set_on_change(self, callback: Callable[[], None]) -> None:
        self._on_change = callback

    def get_jobs(self) -> list[JobRecord]:
        with self._lock:
            return copy.deepcopy(self._jobs)

    def enqueue(self, spec: JobSpec) -> JobRecord:
        record = JobRecord(spec=spec, status="queued", progress_message="Queued.")
        with self._lock:
            self._jobs.append(record)
        self._notify()
        self._wake_event.set()
        return record

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            for job in self._jobs:
                if job.spec.job_id != job_id:
                    continue
                if job.status == "queued":
                    job.status = "cancelled"
                    job.finished_at = _now_iso()
                    job.progress_message = "Cancelled before start."
                    self._notify()
                    return True
                if job.status == "running":
                    job.cancel_requested = True
                    job.progress_message = "Cancellation requested..."
                    if self._active_process and self._active_job_id == job_id:
                        try:
                            self._active_process.terminate()
                        except OSError:
                            pass
                    self._notify()
                    return True
                return False
        return False

    def shutdown(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        self._wake_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=timeout)

    def _notify(self) -> None:
        callback = self._on_change
        if callback is not None:
            callback()

    def _next_queued_job(self) -> JobRecord | None:
        with self._lock:
            for job in self._jobs:
                if job.status == "queued":
                    return job
        return None

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            job = self._next_queued_job()
            if job is None:
                self._wake_event.wait(timeout=0.5)
                self._wake_event.clear()
                continue
            self._run_job(job)

    def _run_job(self, job: JobRecord) -> None:
        with self._lock:
            job.status = "running"
            job.started_at = _now_iso()
            job.progress_message = "Running..."
            self._active_job_id = job.spec.job_id
        self._notify()

        log_path = Path(job.spec.log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with log_path.open("a", encoding="utf-8") as log_file:
                for command in job.spec.commands:
                    if self._stop_event.is_set():
                        self._mark_interrupted(job, "App shutdown.")
                        return
                    if job.cancel_requested:
                        self._mark_cancelled(job, "Cancelled by user.")
                        return

                    with self._lock:
                        job.progress_message = command.description
                    self._notify()

                    log_file.write(
                        f"\n[{_now_iso()}] {command.description}\n$ {' '.join(command.argv)}\n"
                    )
                    log_file.flush()

                    process = subprocess.Popen(
                        command.argv,
                        cwd=self.repo_root,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )

                    with self._lock:
                        self._active_process = process

                    last_line = ""
                    assert process.stdout is not None
                    for line in process.stdout:
                        last_line = line.rstrip()
                        log_file.write(line)
                        log_file.flush()
                        with self._lock:
                            if last_line:
                                job.progress_message = last_line[:300]
                            if job.cancel_requested and process.poll() is None:
                                try:
                                    process.terminate()
                                except OSError:
                                    pass
                        self._notify()

                    return_code = process.wait()
                    with self._lock:
                        self._active_process = None

                    if job.cancel_requested:
                        self._mark_cancelled(job, "Cancelled by user.")
                        return

                    if return_code != 0:
                        message = (
                            last_line[:400]
                            if last_line
                            else f"Command failed with exit code {return_code}."
                        )
                        self._mark_failed(job, return_code, message)
                        return

                with self._lock:
                    job.status = "succeeded"
                    job.exit_code = 0
                    job.finished_at = _now_iso()
                    job.progress_message = "Completed successfully."
                self._notify()
        except OSError as exc:
            self._mark_failed(job, 1, str(exc))
        finally:
            with self._lock:
                self._active_process = None
                self._active_job_id = None

    def _mark_failed(self, job: JobRecord, exit_code: int, message: str) -> None:
        with self._lock:
            job.status = "failed"
            job.exit_code = exit_code
            job.error_summary = message
            job.finished_at = _now_iso()
            job.progress_message = message
        self._notify()

    def _mark_cancelled(self, job: JobRecord, message: str) -> None:
        with self._lock:
            job.status = "cancelled"
            job.finished_at = _now_iso()
            job.progress_message = message
        self._notify()

    def _mark_interrupted(self, job: JobRecord, message: str) -> None:
        with self._lock:
            job.status = "interrupted"
            job.finished_at = _now_iso()
            job.progress_message = message
        self._notify()
