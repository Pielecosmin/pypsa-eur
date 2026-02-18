"""
Run baseline + stress Romania winter 2019 scenarios and generate comparison outputs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    print(f"\n--- {description} ---")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    baseline_cfg = "config/adversarial/romania_2019_winter_baseline.yaml"
    stress_cfg = "config/adversarial/romania_2019_winter_stress.yaml"

    baseline_target = "results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc"
    stress_target = "results/romania-2020-winter-stress/networks/base_s_10_elec_.nc"
    outdir = "results/romania-2020-winter-stress-comparison"

    try:
        run_command(
            ["conda", "run", "-n", "pypsa-eur", "snakemake", "--unlock", "--configfile", baseline_cfg],
            "Unlock baseline workflow",
        )
        run_command(
            [
                "conda",
                "run",
                "-n",
                "pypsa-eur",
                "snakemake",
                "-c",
                "all",
                baseline_target,
                "--configfile",
                baseline_cfg,
            ],
            "Solve baseline scenario",
        )

        run_command(
            ["conda", "run", "-n", "pypsa-eur", "snakemake", "--unlock", "--configfile", stress_cfg],
            "Unlock stress workflow",
        )
        run_command(
            [
                "conda",
                "run",
                "-n",
                "pypsa-eur",
                "snakemake",
                "-c",
                "all",
                stress_target,
                "--configfile",
                stress_cfg,
            ],
            "Solve stress scenario",
        )

        run_command(
            [
                "conda",
                "run",
                "-n",
                "pypsa-eur",
                "python",
                "scripts/report_romania_winter_stress.py",
                "--baseline-net",
                baseline_target,
                "--scenario-net",
                stress_target,
                "--country",
                "RO",
                "--outdir",
                outdir,
            ],
            "Generate comparison report",
        )
    except subprocess.CalledProcessError as exc:
        print(f"\nRun failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

    print("\nCompleted successfully.")
    print(f"- Baseline network: {Path(baseline_target)}")
    print(f"- Stress network:   {Path(stress_target)}")
    print(f"- Report folder:    {Path(outdir)}")


if __name__ == "__main__":
    main()
