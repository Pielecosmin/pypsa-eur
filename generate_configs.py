
import yaml
import os
import copy

# Base config content (simplified from romania.yaml)
base_config = {
    "tutorial": True,
    "run": {
        "name": "romania-test",
        "disable_progressbar": True,
        "shared_resources": {"policy": False}
    },
    "scenario": {
        "clusters": [5],
        "opts": [""]
    },
    "countries": ["RO"],
    "snapshots": {
        "start": "2013-03-01",
        "end": "2013-03-08"
    },
    "electricity": {
        "co2limit_enable": True,
        "co2limit": 100.e+6,
        "extendable_carriers": {
            "Generator": ["solar", "onwind", "offwind-ac", "OCGT", "CCGT", "nuclear"],
            "StorageUnit": ["battery"],
            "Store": ["H2"],
            "Link": ["H2 pipeline"]
        },
        "renewable_carriers": ["solar", "onwind", "offwind-ac"],
        "estimate_renewable_capacities": {
            "enable": True,
            "from_gem": True,
            "year": 2020,
            "expansion_limit": False,
            "technology_mapping": {
                "Offshore": "offwind-ac",
                "Onshore": "onwind",
                "PV": "solar"
            }
        }
    },
    "atlite": {
        "default_cutout": "europe-2013-sarah3-era5",
        "cutouts": {
            "europe-2013-sarah3-era5": {
                "module": ["sarah", "era5"],
                "x": [-12., 42.],
                "y": [33., 72.],
                "dx": 0.3,
                "dy": 0.3,
                "time": ["2013", "2013"]
            }
        }
    },
    "renewable": {
        "offwind-ac": {"max_depth": False},
        "offwind-dc": {"max_depth": False},
        "offwind-float": {"max_depth": False, "min_depth": False}
    },
    "clustering": {
        "exclude_carriers": ["OCGT", "offwind-ac", "coal"],
        "temporal": {"resolution_elec": "24h"}
    },
    "lines": {
        "dynamic_line_rating": {
            "activate": True,
            "max_line_rating": 1.3
        }
    },
    "solving": {
        "solver": {
            "name": "highs",
            "options": "highs-simplex"
        },
        "check_objective": {"enable": False}
    }
}

periods = [
    ("2020-01-01", "2020-01-08", "winter"),
    ("2020-04-01", "2020-04-08", "spring"),
    ("2020-07-01", "2020-07-08", "summer"),
    ("2020-10-01", "2020-10-08", "autumn"),
    ("2020-12-01", "2020-12-08", "december"),
]

for start, end, season in periods:
    cfg = copy.deepcopy(base_config)
    
    # Update Run Name
    cfg["run"]["name"] = f"romania-2020-{season}"
    
    # Update Snapshots
    cfg["snapshots"]["start"] = start
    cfg["snapshots"]["end"] = end
    
    # Update Electricity Year
    # (already 2020 in base, but ensuring)
    cfg["electricity"]["estimate_renewable_capacities"]["year"] = 2020
    
    # Update Atlite Cutouts
    cfg["atlite"]["default_cutout"] = "europe-2020-sarah3-era5"
    cfg["atlite"]["cutouts"] = {
        "europe-2020-sarah3-era5": {
            "module": ["sarah", "era5"],
            "x": [-12., 42.],
            "y": [33., 72.],
            "dx": 0.3,
            "dy": 0.3,
            "time": ["2020", "2020"]
        }
    }
    
    filename = f"config/romania_2020_{season}.yaml"
    with open(filename, 'w') as f:
        yaml.dump(cfg, f, sort_keys=False)
    print(f"Created {filename}")

