from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from scenario_manager.types import ResultEntry

REQUIRED_CSVS = [
    "system_cost_comparison.csv",
    "generation_mix_mwh.csv",
    "lmp_summary_ro.csv",
    "ens_summary.csv",
    "curtailment_mwh.csv",
    "daily_net_imports_mwh.csv",
    "interconnector_flow_congestion.csv",
]


def _safe_mtime(paths: list[Path]) -> float:
    if not paths:
        return 0.0
    return max(path.stat().st_mtime for path in paths if path.exists())


def scan_new_format_results(results_dir: Path) -> list[ResultEntry]:
    entries: list[ResultEntry] = []
    if not results_dir.exists():
        return entries

    for folder in sorted(
        [p for p in results_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    ):
        csv_files = sorted(folder.glob("*.csv"))
        csv_names = [p.name for p in csv_files]
        required_present = all((folder / name).exists() for name in REQUIRED_CSVS)
        if not required_present:
            continue

        png_files = sorted(folder.glob("*.png"))
        assumptions = folder / "assumptions_limitations.md"
        timestamp = _safe_mtime(csv_files + png_files + [assumptions])

        entries.append(
            ResultEntry(
                name=folder.name,
                path=folder,
                timestamp=timestamp,
                required_files_present=required_present,
                csv_files=csv_names,
                figure_files=[p.name for p in png_files],
                assumptions_file=assumptions if assumptions.exists() else None,
            )
        )
    return entries


def parse_summary(result_dir: Path) -> dict[str, str]:
    summary: dict[str, str] = {}

    cost_path = result_dir / "system_cost_comparison.csv"
    ens_path = result_dir / "ens_summary.csv"
    imports_path = result_dir / "daily_net_imports_mwh.csv"
    lmp_path = result_dir / "lmp_summary_ro.csv"

    if cost_path.exists():
        cost_df = pd.read_csv(cost_path)
        if not cost_df.empty:
            row = cost_df.iloc[0]
            summary["baseline_cost"] = f"{row.get('baseline_total_system_cost_eur', 0.0):,.2f}"
            summary["scenario_cost"] = f"{row.get('scenario_total_system_cost_eur', 0.0):,.2f}"
            summary["delta_percent"] = f"{row.get('delta_percent', 0.0):.2f}%"

    if ens_path.exists():
        ens_df = pd.read_csv(ens_path)
        if not ens_df.empty:
            scenario = ens_df[ens_df["case"] == "scenario"]
            if scenario.empty:
                scenario = ens_df.tail(1)
            row = scenario.iloc[0]
            summary["ens_mwh"] = f"{row.get('ens_mwh', 0.0):,.2f}"
            summary["hours_with_shedding"] = str(int(row.get("hours_with_shedding", 0)))
            summary["max_shedding_mw"] = f"{row.get('max_shedding_mw', 0.0):,.2f}"

    if imports_path.exists():
        imports_df = pd.read_csv(imports_path)
        if not imports_df.empty:
            summary["imports_delta_total_mwh"] = (
                f"{imports_df['delta_mwh'].fillna(0.0).sum():,.2f}"
            )

    if lmp_path.exists():
        lmp_df = pd.read_csv(lmp_path)
        if not lmp_df.empty:
            scenario = lmp_df[lmp_df["case"] == "scenario"]
            if scenario.empty:
                scenario = lmp_df.tail(1)
            row = scenario.iloc[0]
            summary["lmp_mean"] = f"{row.get('mean_eur_per_mwh', 0.0):,.4f}"
            summary["lmp_p95"] = f"{row.get('p95_eur_per_mwh', 0.0):,.4f}"
            summary["lmp_max"] = f"{row.get('max_eur_per_mwh', 0.0):,.4f}"

    return summary


def load_csv_preview(csv_path: Path, max_rows: int = 200) -> pd.DataFrame:
    return pd.read_csv(csv_path).head(max_rows)


def list_baseline_networks(results_dir: Path) -> list[Path]:
    return sorted(results_dir.glob("*/networks/base_s_*_elec_.nc"))


def as_row_dicts(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    rows = dataframe.to_dict(orient="records")
    return [dict(row) for row in rows]
