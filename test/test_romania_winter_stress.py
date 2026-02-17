# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT

import numpy as np
import pandas as pd
import pypsa

from scripts.romania_winter_stress import (
    add_import_cap_constraints,
    add_scada_proxy_constraints,
    apply_timeseries_shocks,
)


def _build_shock_network(periods: int = 100) -> pypsa.Network:
    n = pypsa.Network()
    sns = pd.date_range("2019-01-01", periods=periods, freq="h")
    n.set_snapshots(sns)

    n.add("Carrier", "AC")
    n.add("Carrier", "OCGT")
    n.add("Carrier", "hydro")
    n.add("Carrier", "ror")
    n.add("Carrier", "PHS")

    n.add("Bus", "RO_bus", carrier="AC", country="RO")
    n.add("Bus", "BG_bus", carrier="AC", country="BG")

    n.add("Load", "RO_load", bus="RO_bus")
    n.loads_t.p_set = pd.DataFrame(index=sns, data={"RO_load": 100.0})

    n.add("Generator", "RO_ror", bus="RO_bus", carrier="ror", p_nom=80, marginal_cost=2)
    n.add(
        "Generator", "RO_hydro", bus="RO_bus", carrier="hydro", p_nom=120, marginal_cost=3
    )
    n.add(
        "Generator", "RO_ocgt", bus="RO_bus", carrier="OCGT", p_nom=200, marginal_cost=40
    )
    n.add(
        "Generator", "BG_ocgt", bus="BG_bus", carrier="OCGT", p_nom=200, marginal_cost=40
    )

    n.generators_t.p_max_pu = pd.DataFrame(
        index=sns,
        data={c: 1.0 for c in ["RO_ror", "RO_hydro", "RO_ocgt", "BG_ocgt"]},
    )

    n.add("StorageUnit", "RO_phs", bus="RO_bus", carrier="PHS", p_nom=50, max_hours=6)
    n.storage_units_t.inflow = pd.DataFrame(index=sns, data={"RO_phs": 1.0})
    n.storage_units_t.p_max_pu = pd.DataFrame(index=sns, data={"RO_phs": 1.0})

    return n


def _build_constraint_network(periods: int = 100) -> pypsa.Network:
    n = pypsa.Network()
    sns = pd.date_range("2019-01-01", periods=periods, freq="h")
    n.set_snapshots(sns)

    n.add("Carrier", "AC")
    n.add("Carrier", "OCGT")
    n.add("Carrier", "DC")

    n.add("Bus", "RO", carrier="AC", country="RO")
    n.add("Bus", "BG", carrier="AC", country="BG")

    n.add("Generator", "g_ro", bus="RO", carrier="OCGT", p_nom=100, marginal_cost=20)
    n.add("Generator", "g_bg", bus="BG", carrier="OCGT", p_nom=100, marginal_cost=20)
    n.add("Load", "l_ro", bus="RO", p_set=20)

    n.add(
        "Line",
        "line_bg_ro",
        bus0="BG",
        bus1="RO",
        carrier="AC",
        x=0.1,
        r=0.01,
        s_nom=100,
        s_max_pu=1.0,
    )
    n.add(
        "Line",
        "line_ro_bg",
        bus0="RO",
        bus1="BG",
        carrier="AC",
        x=0.1,
        r=0.01,
        s_nom=100,
        s_max_pu=1.0,
    )
    n.add(
        "Link",
        "link_bg_ro",
        bus0="BG",
        bus1="RO",
        carrier="DC",
        p_nom=80,
        p_max_pu=1.0,
        p_min_pu=-1.0,
        efficiency=1.0,
        marginal_cost=0.0,
    )
    n.add(
        "Link",
        "link_ro_bg",
        bus0="RO",
        bus1="BG",
        carrier="DC",
        p_nom=80,
        p_max_pu=1.0,
        p_min_pu=-1.0,
        efficiency=1.0,
        marginal_cost=0.0,
    )
    return n


def test_apply_timeseries_shocks_windows():
    n = _build_shock_network(periods=100)
    cfg = {
        "enable": True,
        "country": "RO",
        "load_factor_full_window": 1.12,
        "hydro_factor_full_window": 0.60,
        "gas_factor_first_72h": 0.70,
    }

    apply_timeseries_shocks(n, n.snapshots, cfg)

    assert np.isclose(n.loads_t.p_set["RO_load"], 112.0).all()
    assert np.isclose(n.generators_t.p_max_pu["RO_ror"], 0.60).all()
    assert np.isclose(n.generators_t.p_max_pu["RO_hydro"], 0.60).all()
    assert np.isclose(n.storage_units_t.inflow["RO_phs"], 0.60).all()
    assert np.isclose(n.storage_units_t.p_max_pu["RO_phs"], 0.60).all()
    assert np.isclose(n.generators_t.p_max_pu["RO_ocgt"].iloc[:72], 0.70).all()
    assert np.isclose(n.generators_t.p_max_pu["RO_ocgt"].iloc[72:], 1.0).all()
    assert np.isclose(n.generators_t.p_max_pu["BG_ocgt"], 1.0).all()


def test_scada_constraints_created():
    n = _build_constraint_network(periods=100)
    n.optimize.create_model()

    cfg = {
        "enable": True,
        "country": "RO",
        "scada": {
            "tight_hours": 24,
            "relaxed_hours": 48,
            "ramp_tight_per_hour": 0.10,
            "ramp_relaxed_per_hour": 0.25,
        },
    }
    add_scada_proxy_constraints(n, n.snapshots, cfg)
    keys = set(n.model.constraints.data.keys())
    assert "ro_scada_ramp_up_tight_fixed" in keys
    assert "ro_scada_ramp_down_tight_fixed" in keys
    assert "ro_scada_ramp_up_relaxed_fixed" in keys
    assert "ro_scada_ramp_down_relaxed_fixed" in keys


def test_import_constraints_directional():
    n = _build_constraint_network(periods=100)
    n.optimize.create_model()

    cfg = {
        "enable": True,
        "country": "RO",
        "import_cap": {"zero_hours": 48, "half_hours": 48, "half_factor": 0.5},
    }
    add_import_cap_constraints(n, n.snapshots, cfg)
    keys = set(n.model.constraints.data.keys())

    assert "ro_import_cap_zero_line_in_pos_fixed" in keys
    assert "ro_import_cap_zero_line_in_neg_fixed" in keys
    assert "ro_import_cap_half_line_in_pos_fixed" in keys
    assert "ro_import_cap_half_line_in_neg_fixed" in keys
    assert "ro_import_cap_zero_link_in_pos_fixed" in keys
    assert "ro_import_cap_zero_link_in_neg_fixed" in keys
    assert "ro_import_cap_half_link_in_pos_fixed" in keys
    assert "ro_import_cap_half_link_in_neg_fixed" in keys


def test_stress_disabled_no_changes():
    n = _build_shock_network(periods=100)
    p_set_before = n.loads_t.p_set.copy()
    p_max_before = n.generators_t.p_max_pu.copy()
    inflow_before = n.storage_units_t.inflow.copy()

    apply_timeseries_shocks(n, n.snapshots, {"enable": False, "country": "RO"})

    pd.testing.assert_frame_equal(n.loads_t.p_set, p_set_before)
    pd.testing.assert_frame_equal(n.generators_t.p_max_pu, p_max_before)
    pd.testing.assert_frame_equal(n.storage_units_t.inflow, inflow_before)
