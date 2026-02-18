"""
Run baseline + stress Romania winter 2020 scenarios and generate comparison outputs.
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    baseline_cfg = "config/adversarial/romania_2019_winter_baseline.yaml"
    stress_cfg = "config/adversarial/romania_2019_winter_stress.yaml"

    baseline_target = "results/romania-2020-winter-baseline/networks/base_s_10_elec_.nc"
    stress_target = "results/romania-2020-winter-stress/networks/base_s_10_elec_.nc"
    outdir = "results/romania-2020-winter-stress-comparison"

    try:
        # Import snakemake programmatically
        from snakemake import snakemake

        logger.info("--- Unlock baseline workflow ---")
        snakemake(
            configfiles=[baseline_cfg],
            unlock=True,
            quiet=False,
        )

        logger.info("--- Solve baseline scenario ---")
        success_baseline = snakemake(
            configfiles=[baseline_cfg],
            targets=[baseline_target],
            cores="all",
            quiet=False,
        )
        
        if not success_baseline:
            raise RuntimeError("Baseline scenario solve failed")
        
        logger.info("--- Unlock stress workflow ---")
        snakemake(
            configfiles=[stress_cfg],
            unlock=True,
            quiet=False,
        )

        logger.info("--- Solve stress scenario ---")
        success_stress = snakemake(
            configfiles=[stress_cfg],
            targets=[stress_target],
            cores="all",
            quiet=False,
        )
        
        if not success_stress:
            raise RuntimeError("Stress scenario solve failed")

        logger.info("--- Generate comparison report ---")
        import subprocess
        result = subprocess.run(
            [
                sys.executable,
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
            check=True,
        )

    except Exception as exc:
        logger.error(f"\nRun failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("\nCompleted successfully.")
    logger.info(f"- Baseline network: {Path(baseline_target)}")
    logger.info(f"- Stress network:   {Path(stress_target)}")
    logger.info(f"- Report folder:    {Path(outdir)}")


if __name__ == "__main__":
    main()
