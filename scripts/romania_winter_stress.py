# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT
"""
Helpers for the Romania winter 2019 stress scenario.
"""

from __future__ import annotations

import logging

import pandas as pd
import pypsa
import xarray as xr

logger = logging.getLogger(__name__)
PYPSA_V1 = int(pypsa.__version__.split(".", maxsplit=1)[0]) >= 1

VARIABLE_RENEWABLE_CARRIERS = {
    "solar",
    "solar-hsat",
    "solar rooftop",
    "onwind",
    "offwind-ac",
    "offwind-dc",
    "offwind-float",
    "ror",
}


def _component_dim(da: xr.DataArray, component: str) -> str:
    if component in da.dims:
        return component
    extended = f"{component}-ext"
    if extended in da.dims:
        return extended
    if PYPSA_V1 and "name" in da.dims:
        return "name"
    for dim in da.dims:
        if dim.lower().startswith(component.lower()):
            return dim
    raise KeyError(f"Unable to find component dimension for {component} in {da.dims}")


def _time_window(snapshots: pd.DatetimeIndex, start: int, length: int) -> pd.DatetimeIndex:
    if length <= 0 or start >= len(snapshots):
        return pd.DatetimeIndex([], name=snapshots.name)
    return snapshots[start : start + length]


def _country_index(
    n: pypsa.Network, component: str, bus_column: str, country: str
) -> pd.Index:
    df = getattr(n, component)
    countries = df[bus_column].map(n.buses.country)
    return df.index[countries == country]


def _scale_columns(
    table: pd.DataFrame, snapshots: pd.DatetimeIndex, columns: pd.Index, factor: float
) -> None:
    if table.empty:
        return
    cols = table.columns.intersection(columns)
    if cols.empty:
        return
    table.loc[snapshots, cols] = table.loc[snapshots, cols] * factor


def _capacity_expression(
    n: pypsa.Network, component: str, index: pd.Index, target_dim: str
) -> tuple[pd.Index, xr.DataArray, pd.Index, xr.DataArray]:
    if component == "Line":
        df = n.lines
        nominal_col = "s_nom"
        nominal_opt_col = "s_nom_opt"
        extendable_col = "s_nom_extendable"
        variable_name = "Line-s_nom"
        scale = df["s_max_pu"].reindex(index).fillna(1.0)
    elif component == "Link":
        df = n.links
        nominal_col = "p_nom"
        nominal_opt_col = "p_nom_opt"
        extendable_col = "p_nom_extendable"
        variable_name = "Link-p_nom"
        scale = pd.Series(1.0, index=index)
    else:
        raise ValueError(f"Unsupported component '{component}'")

    fixed_i = index.difference(df.index[df[extendable_col]])
    ext_i = index.intersection(df.index[df[extendable_col]])

    fixed_capacity = df[nominal_opt_col].where(df[nominal_opt_col].notna(), df[nominal_col])
    fixed_capacity = fixed_capacity.reindex(fixed_i).fillna(df.loc[fixed_i, nominal_col])
    rhs_fixed = xr.DataArray(
        fixed_capacity * scale.reindex(fixed_i).fillna(1.0),
        dims=[target_dim],
        coords={target_dim: fixed_i},
    )

    rhs_ext = xr.DataArray([], dims=[target_dim], coords={target_dim: []})
    if len(ext_i):
        cap_var = n.model[variable_name]
        cap_dim = _component_dim(cap_var, component)
        rhs_ext = cap_var.sel({cap_dim: ext_i})
        if cap_dim != target_dim:
            rhs_ext = rhs_ext.rename({cap_dim: target_dim})
        rhs_ext = rhs_ext * xr.DataArray(
            scale.reindex(ext_i).fillna(1.0),
            dims=[target_dim],
            coords={target_dim: ext_i},
        )

    return fixed_i, rhs_fixed, ext_i, rhs_ext


def apply_timeseries_shocks(
    n: pypsa.Network, snapshots: pd.DatetimeIndex, cfg: dict
) -> None:
    """
    Apply RO-only demand/hydro/gas timeseries shocks before model creation.
    """
    if not cfg.get("enable", False):
        return

    country = cfg.get("country", "RO")
    snapshots = pd.DatetimeIndex(snapshots)

    load_factor = float(cfg.get("load_factor_full_window", 1.0))
    hydro_factor = float(cfg.get("hydro_factor_full_window", 1.0))
    gas_factor = float(cfg.get("gas_factor_first_72h", 1.0))

    ro_loads = _country_index(n, "loads", "bus", country)
    if ro_loads.empty:
        logger.warning("Stress scenario: no RO loads found for demand scaling.")
    else:
        _scale_columns(n.loads_t.p_set, snapshots, ro_loads, load_factor)

    ro_hydro_gens = n.generators.index[
        (n.generators.bus.map(n.buses.country) == country)
        & (n.generators.carrier.isin(["ror", "hydro"]))
    ]
    if ro_hydro_gens.empty:
        logger.warning(
            "Stress scenario: no RO hydro generators ('ror'/'hydro') found for availability scaling."
        )
    else:
        _scale_columns(n.generators_t.p_max_pu, snapshots, ro_hydro_gens, hydro_factor)
        _scale_columns(n.generators_t.p_min_pu, snapshots, ro_hydro_gens, hydro_factor)

    ro_hydro_storage = n.storage_units.index[
        (n.storage_units.bus.map(n.buses.country) == country)
        & (n.storage_units.carrier.isin(["hydro", "PHS"]))
    ]
    if ro_hydro_storage.empty:
        logger.warning(
            "Stress scenario: no RO hydro storage units ('hydro'/'PHS') found for inflow scaling."
        )
    else:
        _scale_columns(
            n.storage_units_t.inflow, snapshots, ro_hydro_storage, hydro_factor
        )
        if hasattr(n.storage_units_t, "p_max_pu"):
            _scale_columns(
                n.storage_units_t.p_max_pu, snapshots, ro_hydro_storage, hydro_factor
            )

    gas_snapshots = _time_window(snapshots, 0, 72)
    ro_gas_gens = n.generators.index[
        (n.generators.bus.map(n.buses.country) == country)
        & (n.generators.carrier.isin(["OCGT", "CCGT"]))
    ]
    if ro_gas_gens.empty:
        logger.warning(
            "Stress scenario: no RO gas generators ('OCGT'/'CCGT') found for first-72h availability scaling."
        )
    else:
        _scale_columns(n.generators_t.p_max_pu, gas_snapshots, ro_gas_gens, gas_factor)


def add_scada_proxy_constraints(
    n: pypsa.Network, snapshots: pd.DatetimeIndex, cfg: dict
) -> None:
    """
    Add RO-only ramp degradation proxy constraints for the first 72 hours.
    """
    if not cfg.get("enable", False):
        return

    country = cfg.get("country", "RO")
    scada_cfg = cfg.get("scada", {})
    tight_hours = int(scada_cfg.get("tight_hours", 24))
    relaxed_hours = int(scada_cfg.get("relaxed_hours", 48))
    ramp_tight = float(scada_cfg.get("ramp_tight_per_hour", 0.10))
    ramp_relaxed = float(scada_cfg.get("ramp_relaxed_per_hour", 0.25))

    snapshots = pd.DatetimeIndex(snapshots)
    if len(snapshots) < 2:
        return

    ro_mask = n.generators.bus.map(n.buses.country) == country
    controllable = n.generators.index[
        ro_mask
        & ~n.generators.carrier.isin(VARIABLE_RENEWABLE_CARRIERS | {"load", "curtailment"})
    ]
    if controllable.empty:
        logger.warning(
            "Stress scenario: no controllable RO generators found for SCADA proxy constraints."
        )
        return

    p = n.model["Generator-p"]
    gen_dim = _component_dim(p, "Generator")
    p = p.sel({gen_dim: controllable})

    fixed_i = controllable.difference(n.generators.index[n.generators.p_nom_extendable])
    ext_i = controllable.intersection(n.generators.index[n.generators.p_nom_extendable])

    p_nom = None
    if len(ext_i):
        try:
            p_nom = n.model["Generator-p_nom"]
            p_nom_dim = _component_dim(p_nom, "Generator")
            p_nom = p_nom.sel({p_nom_dim: ext_i})
            if p_nom_dim != gen_dim:
                p_nom = p_nom.rename({p_nom_dim: gen_dim})
        except KeyError:
            logger.warning(
                "Stress scenario: missing Generator-p_nom variable for extendable SCADA set, skipping extendable ramp constraints."
            )
            ext_i = pd.Index([])

    windows = [
        ("tight", _time_window(snapshots, 1, tight_hours), ramp_tight),
        (
            "relaxed",
            _time_window(snapshots, 1 + tight_hours, relaxed_hours),
            ramp_relaxed,
        ),
    ]

    for label, current, ramp in windows:
        if current.empty:
            continue

        prev = snapshots[snapshots.get_indexer(current) - 1]
        p_curr = p.sel(snapshot=current)
        p_prev = p.sel(snapshot=prev).assign_coords(snapshot=current)
        delta = p_curr - p_prev

        if len(fixed_i):
            fixed_rhs = xr.DataArray(
                n.generators.loc[fixed_i, "p_nom"] * ramp,
                dims=[gen_dim],
                coords={gen_dim: fixed_i},
            )
            fixed_delta = delta.sel({gen_dim: fixed_i})
            n.model.add_constraints(
                fixed_delta <= fixed_rhs,
                name=f"ro_scada_ramp_up_{label}_fixed",
            )
            n.model.add_constraints(
                -fixed_delta <= fixed_rhs,
                name=f"ro_scada_ramp_down_{label}_fixed",
            )

        if len(ext_i):
            ext_rhs = p_nom * ramp
            ext_delta = delta.sel({gen_dim: ext_i})
            n.model.add_constraints(
                ext_delta <= ext_rhs,
                name=f"ro_scada_ramp_up_{label}_ext",
            )
            n.model.add_constraints(
                -ext_delta <= ext_rhs,
                name=f"ro_scada_ramp_down_{label}_ext",
            )


def _add_one_sided_import_cap(
    n: pypsa.Network,
    component: str,
    variable: xr.DataArray,
    target_dim: str,
    assets: pd.Index,
    time_window: pd.DatetimeIndex,
    factor: float,
    direction: int,
    name: str,
) -> None:
    if assets.empty or time_window.empty:
        return

    fixed_i, rhs_fixed, ext_i, rhs_ext = _capacity_expression(n, component, assets, target_dim)

    if len(fixed_i):
        lhs_fixed = direction * variable.sel(snapshot=time_window, **{target_dim: fixed_i})
        n.model.add_constraints(lhs_fixed <= rhs_fixed * factor, name=f"{name}_fixed")

    if len(ext_i):
        lhs_ext = direction * variable.sel(snapshot=time_window, **{target_dim: ext_i})
        n.model.add_constraints(lhs_ext <= rhs_ext * factor, name=f"{name}_ext")


def add_import_cap_constraints(
    n: pypsa.Network, snapshots: pd.DatetimeIndex, cfg: dict
) -> None:
    """
    Add RO border import caps: 0% (first 48h), 50% (next 48h).
    """
    if not cfg.get("enable", False):
        return

    country = cfg.get("country", "RO")
    import_cfg = cfg.get("import_cap", {})
    zero_hours = int(import_cfg.get("zero_hours", 48))
    half_hours = int(import_cfg.get("half_hours", 48))
    half_factor = float(import_cfg.get("half_factor", 0.5))

    snapshots = pd.DatetimeIndex(snapshots)
    zero_window = _time_window(snapshots, 0, zero_hours)
    half_window = _time_window(snapshots, zero_hours, half_hours)

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

    if line_border.empty and link_border.empty:
        logger.warning(
            "Stress scenario: no RO border interconnectors found; import cap constraints were not added."
        )
        return

    if not line_border.empty:
        line_var = n.model["Line-s"]
        line_dim = _component_dim(line_var, "Line")

        c0 = n.lines.bus0.map(n.buses.country)
        c1 = n.lines.bus1.map(n.buses.country)
        inbound_pos = line_border[(c1.loc[line_border] == country).values]
        inbound_neg = line_border[(c0.loc[line_border] == country).values]

        _add_one_sided_import_cap(
            n,
            component="Line",
            variable=line_var,
            target_dim=line_dim,
            assets=inbound_pos,
            time_window=zero_window,
            factor=0.0,
            direction=1,
            name="ro_import_cap_zero_line_in_pos",
        )
        _add_one_sided_import_cap(
            n,
            component="Line",
            variable=line_var,
            target_dim=line_dim,
            assets=inbound_neg,
            time_window=zero_window,
            factor=0.0,
            direction=-1,
            name="ro_import_cap_zero_line_in_neg",
        )
        _add_one_sided_import_cap(
            n,
            component="Line",
            variable=line_var,
            target_dim=line_dim,
            assets=inbound_pos,
            time_window=half_window,
            factor=half_factor,
            direction=1,
            name="ro_import_cap_half_line_in_pos",
        )
        _add_one_sided_import_cap(
            n,
            component="Line",
            variable=line_var,
            target_dim=line_dim,
            assets=inbound_neg,
            time_window=half_window,
            factor=half_factor,
            direction=-1,
            name="ro_import_cap_half_line_in_neg",
        )

    if not link_border.empty:
        link_var = n.model["Link-p"]
        link_dim = _component_dim(link_var, "Link")

        c0 = n.links.bus0.map(n.buses.country)
        c1 = n.links.bus1.map(n.buses.country)
        inbound_pos = link_border[(c1.loc[link_border] == country).values]
        inbound_neg = link_border[(c0.loc[link_border] == country).values]

        _add_one_sided_import_cap(
            n,
            component="Link",
            variable=link_var,
            target_dim=link_dim,
            assets=inbound_pos,
            time_window=zero_window,
            factor=0.0,
            direction=1,
            name="ro_import_cap_zero_link_in_pos",
        )
        _add_one_sided_import_cap(
            n,
            component="Link",
            variable=link_var,
            target_dim=link_dim,
            assets=inbound_neg,
            time_window=zero_window,
            factor=0.0,
            direction=-1,
            name="ro_import_cap_zero_link_in_neg",
        )
        _add_one_sided_import_cap(
            n,
            component="Link",
            variable=link_var,
            target_dim=link_dim,
            assets=inbound_pos,
            time_window=half_window,
            factor=half_factor,
            direction=1,
            name="ro_import_cap_half_link_in_pos",
        )
        _add_one_sided_import_cap(
            n,
            component="Link",
            variable=link_var,
            target_dim=link_dim,
            assets=inbound_neg,
            time_window=half_window,
            factor=half_factor,
            direction=-1,
            name="ro_import_cap_half_link_in_neg",
        )
