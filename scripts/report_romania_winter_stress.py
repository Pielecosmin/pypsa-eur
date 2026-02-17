# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT
"""
Generate baseline vs stress comparison outputs for the Romania winter 2019 stress run.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pypsa


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-net", required=True, help="Path to baseline solved network.")
    parser.add_argument("--scenario-net", required=True, help="Path to stress solved network.")
    parser.add_argument("--country", default="RO", help="Country code for reporting.")
    parser.add_argument(
        "--outdir",
        default="results/romania-2019-winter-stress-comparison",
        help="Output directory.",
    )
    return parser.parse_args()


def weights(n: pypsa.Network) -> pd.Series:
    return n.snapshot_weightings.generators.reindex(n.snapshots).fillna(1.0)


def total_system_cost(n: pypsa.Network) -> float:
    objective = getattr(n, "objective", np.nan)
    if pd.notna(objective):
        return float(objective)
    return float(n.statistics.capex().sum() + n.statistics.opex().sum())


def ro_shedding_series(n: pypsa.Network, country: str) -> pd.Series:
    shedding_i = n.generators.index[
        (n.generators.carrier == "load") & (n.generators.bus.map(n.buses.country) == country)
    ]
    if shedding_i.empty or n.generators_t.p.empty:
        return pd.Series(0.0, index=n.snapshots)
    return n.generators_t.p[shedding_i].sum(axis=1).reindex(n.snapshots).fillna(0.0)


def ens_metrics(n: pypsa.Network, country: str) -> dict[str, float]:
    shedding_mw = ro_shedding_series(n, country)
    w = weights(n)
    ens_mwh = float((shedding_mw * w).sum())
    return {
        "ens_mwh": ens_mwh,
        "hours_with_shedding": int((shedding_mw > 1e-6).sum()),
        "max_shedding_mw": float(shedding_mw.max()),
    }


def _border_assets(n: pypsa.Network, country: str) -> tuple[pd.Index, pd.Index]:
    line_border = pd.Index([])
    link_border = pd.Index([])
    if not n.lines.empty:
        c0 = n.lines.bus0.map(n.buses.country)
        c1 = n.lines.bus1.map(n.buses.country)
        line_border = n.lines.index[(c0 == country) ^ (c1 == country)]
    if not n.links.empty:
        c0 = n.links.bus0.map(n.buses.country)
        c1 = n.links.bus1.map(n.buses.country)
        link_border = n.links.index[(c0 == country) ^ (c1 == country)]
    return line_border, link_border


def net_import_series(n: pypsa.Network, country: str) -> pd.Series:
    imports = pd.Series(0.0, index=n.snapshots)
    line_border, link_border = _border_assets(n, country)

    if not line_border.empty and hasattr(n.lines_t, "p0") and not n.lines_t.p0.empty:
        p0 = n.lines_t.p0.reindex(index=n.snapshots, columns=line_border).fillna(0.0)
        sign = pd.Series(index=line_border, dtype=float)
        sign[n.lines.loc[line_border, "bus1"].map(n.buses.country) == country] = 1.0
        sign[n.lines.loc[line_border, "bus0"].map(n.buses.country) == country] = -1.0
        imports = imports + p0.mul(sign, axis=1).sum(axis=1)

    if not link_border.empty and hasattr(n.links_t, "p0") and not n.links_t.p0.empty:
        p0 = n.links_t.p0.reindex(index=n.snapshots, columns=link_border).fillna(0.0)
        sign = pd.Series(index=link_border, dtype=float)
        sign[n.links.loc[link_border, "bus1"].map(n.buses.country) == country] = 1.0
        sign[n.links.loc[link_border, "bus0"].map(n.buses.country) == country] = -1.0
        imports = imports + p0.mul(sign, axis=1).sum(axis=1)

    return imports


def daily_imports_mwh(n: pypsa.Network, country: str) -> pd.Series:
    imp_mwh = net_import_series(n, country) * weights(n)
    local_index = pd.DatetimeIndex(imp_mwh.index).tz_localize("UTC").tz_convert(
        "Europe/Bucharest"
    )
    imp_local = pd.Series(imp_mwh.values, index=local_index)
    daily = imp_local.groupby(pd.Grouper(freq="D")).sum()
    daily.index = daily.index.date
    return daily


def interconnector_congestion(n: pypsa.Network, country: str, case_name: str) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    w = weights(n)
    line_border, link_border = _border_assets(n, country)

    if not line_border.empty and hasattr(n.lines_t, "p0") and not n.lines_t.p0.empty:
        flow = n.lines_t.p0.reindex(index=n.snapshots, columns=line_border).fillna(0.0).abs()
        cap = (
            n.lines["s_nom_opt"].where(n.lines["s_nom_opt"].notna(), n.lines["s_nom"])
            * n.lines["s_max_pu"].fillna(1.0)
        ).reindex(line_border)
        loading = flow.divide(cap.replace(0.0, np.nan), axis=1)
        for asset in line_border:
            s = loading[asset].dropna()
            rows.append(
                {
                    "case": case_name,
                    "component": "Line",
                    "asset": asset,
                    "mean_loading": float(s.mean()) if not s.empty else np.nan,
                    "p95_loading": float(s.quantile(0.95)) if not s.empty else np.nan,
                    "max_loading": float(s.max()) if not s.empty else np.nan,
                    "congested_hours": int((s > 0.95).sum()) if not s.empty else 0,
                    "total_abs_flow_mwh": float((flow[asset] * w).sum()),
                }
            )

    if not link_border.empty and hasattr(n.links_t, "p0") and not n.links_t.p0.empty:
        flow = n.links_t.p0.reindex(index=n.snapshots, columns=link_border).fillna(0.0).abs()
        cap = n.links["p_nom_opt"].where(n.links["p_nom_opt"].notna(), n.links["p_nom"]).reindex(
            link_border
        )
        loading = flow.divide(cap.replace(0.0, np.nan), axis=1)
        for asset in link_border:
            s = loading[asset].dropna()
            rows.append(
                {
                    "case": case_name,
                    "component": "Link",
                    "asset": asset,
                    "mean_loading": float(s.mean()) if not s.empty else np.nan,
                    "p95_loading": float(s.quantile(0.95)) if not s.empty else np.nan,
                    "max_loading": float(s.max()) if not s.empty else np.nan,
                    "congested_hours": int((s > 0.95).sum()) if not s.empty else 0,
                    "total_abs_flow_mwh": float((flow[asset] * w).sum()),
                }
            )

    return pd.DataFrame(rows)


def generation_mix_mwh(n: pypsa.Network, country: str, case_name: str) -> pd.DataFrame:
    w = weights(n)
    rows: list[dict[str, str | float]] = []

    ro_gens = n.generators.index[n.generators.bus.map(n.buses.country) == country]
    if not ro_gens.empty and not n.generators_t.p.empty:
        gen = n.generators_t.p.reindex(index=n.snapshots, columns=ro_gens).fillna(0.0)
        gen_mwh = gen.clip(lower=0.0).mul(w, axis=0).sum(axis=0)
        by_carrier = gen_mwh.groupby(n.generators.loc[ro_gens, "carrier"]).sum()
        rows.extend(
            {"case": case_name, "carrier": carrier, "generation_mwh": float(val)}
            for carrier, val in by_carrier.items()
        )

    ro_su = n.storage_units.index[n.storage_units.bus.map(n.buses.country) == country]
    if not ro_su.empty:
        if hasattr(n.storage_units_t, "p_dispatch") and not n.storage_units_t.p_dispatch.empty:
            su = n.storage_units_t.p_dispatch.reindex(index=n.snapshots, columns=ro_su).fillna(0.0)
        elif hasattr(n.storage_units_t, "p") and not n.storage_units_t.p.empty:
            su = n.storage_units_t.p.reindex(index=n.snapshots, columns=ro_su).fillna(0.0)
            su = su.clip(lower=0.0)
        else:
            su = pd.DataFrame(index=n.snapshots, columns=ro_su, data=0.0)
        su_mwh = su.mul(w, axis=0).sum(axis=0)
        by_carrier = su_mwh.groupby(n.storage_units.loc[ro_su, "carrier"]).sum()
        rows.extend(
            {"case": case_name, "carrier": carrier, "generation_mwh": float(val)}
            for carrier, val in by_carrier.items()
        )

    if not rows:
        return pd.DataFrame(columns=["case", "carrier", "generation_mwh"])
    return pd.DataFrame(rows).groupby(["case", "carrier"], as_index=False).sum()


def curtailment_mwh(n: pypsa.Network, country: str, case_name: str) -> pd.DataFrame:
    ro_gens = n.generators.index[n.generators.bus.map(n.buses.country) == country]
    if ro_gens.empty or n.generators_t.p.empty or n.generators_t.p_max_pu.empty:
        return pd.DataFrame(columns=["case", "carrier", "curtailment_mwh"])

    ro_gens = n.generators_t.p_max_pu.columns.intersection(ro_gens)
    if ro_gens.empty:
        return pd.DataFrame(columns=["case", "carrier", "curtailment_mwh"])

    w = weights(n)
    p_nom = n.generators["p_nom_opt"].where(n.generators["p_nom_opt"].notna(), n.generators["p_nom"])
    available = n.generators_t.p_max_pu[ro_gens].mul(p_nom.reindex(ro_gens), axis=1)
    actual = n.generators_t.p.reindex(index=n.snapshots, columns=ro_gens).fillna(0.0).clip(lower=0.0)
    curt = (available - actual).clip(lower=0.0)
    curt_mwh = curt.mul(w, axis=0).sum(axis=0)
    by_carrier = curt_mwh.groupby(n.generators.loc[ro_gens, "carrier"]).sum()
    return pd.DataFrame(
        {
            "case": case_name,
            "carrier": by_carrier.index,
            "curtailment_mwh": by_carrier.values.astype(float),
        }
    )


def lmp_summary(n: pypsa.Network, country: str, case_name: str) -> pd.DataFrame:
    ro_buses = n.buses.index[n.buses.country == country]
    if ro_buses.empty or n.buses_t.marginal_price.empty:
        return pd.DataFrame(columns=["case", "mean_eur_per_mwh", "p95_eur_per_mwh", "max_eur_per_mwh"])
    prices = n.buses_t.marginal_price.reindex(index=n.snapshots, columns=ro_buses).values.flatten()
    prices = prices[np.isfinite(prices)]
    if prices.size == 0:
        return pd.DataFrame(columns=["case", "mean_eur_per_mwh", "p95_eur_per_mwh", "max_eur_per_mwh"])
    return pd.DataFrame(
        [
            {
                "case": case_name,
                "mean_eur_per_mwh": float(np.mean(prices)),
                "p95_eur_per_mwh": float(np.quantile(prices, 0.95)),
                "max_eur_per_mwh": float(np.max(prices)),
            }
        ]
    )


def _save_figure(fig: plt.Figure, base_path: Path) -> None:
    fig.savefig(base_path.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(base_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _write_assumptions_note(outdir: Path, country: str, has_interconnectors: bool) -> None:
    text = f"""# Romania Winter 2019 Stress Scenario: Assumptions and Limitations

## Scope and time definition
- Geography modeled: RO, BG, HU, RS.
- Stress applied only to country `{country}`.
- Snapshot window in UTC: **2019-01-13 22:00 to 2019-01-20 22:00** (`inclusive: left`, 168 hourly snapshots).
- Equivalent local window in Europe/Bucharest (EET): **2019-01-14 00:00 to 2019-01-21 00:00**.

## Stress assumptions implemented
- Demand shock (RO): +12% over the full 168 hours.
- Hydro availability shock (RO): 60% of baseline availability/inflow over full window.
- Gas availability shock (RO OCGT/CCGT): 70% of baseline for first 72 hours.
- SCADA proxy:
  - Hours 1-24: `|p_t - p_{{t-1}}| <= 0.10 * p_nom_effective`
  - Hours 25-72: `|p_t - p_{{t-1}}| <= 0.25 * p_nom_effective`
  - `p_nom_effective` is fixed nominal for non-extendable units and decision variable for extendable units.
- Import cap proxy on RO border assets:
  - First 48 hours: inbound cap at 0% of available interconnector capacity.
  - Next 48 hours: inbound cap at 50%.
  - Remaining 72 hours: no additional import cap.

## Modeling and interpretation limits
- Load shedding is represented via high-penalty virtual generation (`100000 EUR/MWh`), interpreted as ENS.
- Daily import/export reporting is aggregated in local time (Europe/Bucharest) while snapshots are solved in UTC.
- Congestion is reported using absolute loading ratio against optimized nominal capacity.
"""
    if not has_interconnectors:
        text += "\n- No RO border interconnectors were found in the solved network; import-cap effects are therefore not observable in flow metrics.\n"
    outdir.joinpath("assumptions_limitations.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    baseline = pypsa.Network(args.baseline_net)
    scenario = pypsa.Network(args.scenario_net)
    country = args.country

    baseline_shed = ro_shedding_series(baseline, country)
    scenario_shed = ro_shedding_series(scenario, country)

    ens_df = pd.DataFrame(
        [
            {"case": "baseline", **ens_metrics(baseline, country)},
            {"case": "scenario", **ens_metrics(scenario, country)},
        ]
    )
    ens_df.to_csv(outdir / "ens_summary.csv", index=False)

    cost_baseline = total_system_cost(baseline)
    cost_scenario = total_system_cost(scenario)
    cost_df = pd.DataFrame(
        [
            {
                "baseline_total_system_cost_eur": cost_baseline,
                "scenario_total_system_cost_eur": cost_scenario,
                "delta_eur": cost_scenario - cost_baseline,
                "delta_percent": (cost_scenario - cost_baseline) / cost_baseline * 100
                if cost_baseline != 0
                else np.nan,
            }
        ]
    )
    cost_df.to_csv(outdir / "system_cost_comparison.csv", index=False)

    daily_baseline = daily_imports_mwh(baseline, country)
    daily_scenario = daily_imports_mwh(scenario, country)
    daily_df = pd.DataFrame(
        {
            "local_day": sorted(set(daily_baseline.index) | set(daily_scenario.index)),
        }
    )
    daily_df["baseline_mwh"] = daily_df["local_day"].map(daily_baseline).fillna(0.0)
    daily_df["scenario_mwh"] = daily_df["local_day"].map(daily_scenario).fillna(0.0)
    daily_df["delta_mwh"] = daily_df["scenario_mwh"] - daily_df["baseline_mwh"]
    daily_df.to_csv(outdir / "daily_net_imports_mwh.csv", index=False)

    congestion_df = pd.concat(
        [
            interconnector_congestion(baseline, country, "baseline"),
            interconnector_congestion(scenario, country, "scenario"),
        ],
        ignore_index=True,
    )
    congestion_df.to_csv(outdir / "interconnector_flow_congestion.csv", index=False)

    mix_df = pd.concat(
        [
            generation_mix_mwh(baseline, country, "baseline"),
            generation_mix_mwh(scenario, country, "scenario"),
        ],
        ignore_index=True,
    )
    mix_df.to_csv(outdir / "generation_mix_mwh.csv", index=False)

    curt_df = pd.concat(
        [
            curtailment_mwh(baseline, country, "baseline"),
            curtailment_mwh(scenario, country, "scenario"),
        ],
        ignore_index=True,
    )
    curt_df.to_csv(outdir / "curtailment_mwh.csv", index=False)

    lmp_df = pd.concat(
        [lmp_summary(baseline, country, "baseline"), lmp_summary(scenario, country, "scenario")],
        ignore_index=True,
    )
    lmp_df.to_csv(outdir / "lmp_summary_ro.csv", index=False)

    # Figure 1: Shedding timeseries
    local_index = pd.DatetimeIndex(baseline_shed.index).tz_localize("UTC").tz_convert(
        "Europe/Bucharest"
    )
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(local_index, baseline_shed.values, label="Baseline", linewidth=1.6)
    ax.plot(local_index, scenario_shed.values, label="Scenario", linewidth=1.6)
    ax.set_ylabel("Load Shedding (MW)")
    ax.set_title(f"{country} Load Shedding Timeseries")
    ax.grid(alpha=0.3)
    ax.legend()
    _save_figure(fig, outdir / "fig_01_shedding_timeseries")

    # Figure 2: Daily net imports
    fig, ax = plt.subplots(figsize=(8, 4))
    days = pd.to_datetime(daily_df["local_day"])
    ax.plot(days, daily_df["baseline_mwh"], marker="o", label="Baseline")
    ax.plot(days, daily_df["scenario_mwh"], marker="o", label="Scenario")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_ylabel("Net Imports (MWh/day)")
    ax.set_title(f"{country} Daily Net Imports")
    ax.grid(alpha=0.3)
    ax.legend()
    _save_figure(fig, outdir / "fig_02_daily_net_imports")

    # Figure 3: Generation mix
    fig, ax = plt.subplots(figsize=(10, 5))
    if mix_df.empty:
        ax.text(0.5, 0.5, "No generation mix data", ha="center", va="center")
        ax.axis("off")
    else:
        pivot = (
            mix_df.pivot_table(index="case", columns="carrier", values="generation_mwh", aggfunc="sum")
            .fillna(0.0)
            .sort_index(axis=1)
        )
        pivot.plot(kind="bar", stacked=True, ax=ax)
        ax.set_ylabel("Generation (MWh)")
        ax.set_title(f"{country} Generation Mix")
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    _save_figure(fig, outdir / "fig_03_generation_mix")

    # Figure 4: Interconnector loading
    fig, ax = plt.subplots(figsize=(10, 5))
    if congestion_df.empty:
        ax.text(0.5, 0.5, "No border interconnectors in solved network", ha="center", va="center")
        ax.axis("off")
    else:
        plot_df = congestion_df.copy()
        plot_df["asset_label"] = plot_df["component"] + ":" + plot_df["asset"]
        pivot = plot_df.pivot_table(
            index="asset_label", columns="case", values="mean_loading", aggfunc="mean"
        ).fillna(0.0)
        pivot.sort_values(by=pivot.columns.tolist(), ascending=False).plot(kind="bar", ax=ax)
        ax.set_ylabel("Mean Loading (p.u.)")
        ax.set_title(f"{country} Border Interconnector Mean Loading")
        ax.grid(axis="y", alpha=0.3)
    _save_figure(fig, outdir / "fig_04_interconnector_loading")

    # Figure 5: LMP distribution (if available)
    if not lmp_df.empty:
        ro_buses_base = baseline.buses.index[baseline.buses.country == country]
        ro_buses_scen = scenario.buses.index[scenario.buses.country == country]
        p_base = (
            baseline.buses_t.marginal_price.reindex(columns=ro_buses_base).values.flatten()
            if not baseline.buses_t.marginal_price.empty
            else np.array([])
        )
        p_scen = (
            scenario.buses_t.marginal_price.reindex(columns=ro_buses_scen).values.flatten()
            if not scenario.buses_t.marginal_price.empty
            else np.array([])
        )
        p_base = p_base[np.isfinite(p_base)]
        p_scen = p_scen[np.isfinite(p_scen)]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.boxplot(
            [p_base, p_scen], tick_labels=["Baseline", "Scenario"], showfliers=False
        )
        ax.set_ylabel("Marginal Price (EUR/MWh)")
        ax.set_title(f"{country} Price Distribution")
        ax.grid(axis="y", alpha=0.3)
        _save_figure(fig, outdir / "fig_05_ro_price_distribution")

    _write_assumptions_note(
        outdir=outdir,
        country=country,
        has_interconnectors=not congestion_df.empty,
    )

    print(f"Comparison outputs written to {outdir}")


if __name__ == "__main__":
    main()
