"""
Generate 10 Adversarial Scenario Configurations for Romania
============================================================
Stress-test scenarios simulating infrastructure failures and extreme conditions.
"""

import yaml
import os
import copy

# Create output directory
OUTPUT_DIR = "config/adversarial"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Base configuration (December 2020 - winter stress period)
BASE_CONFIG = {
    "tutorial": True,
    "run": {
        "name": "romania-adversarial-base",
        "disable_progressbar": True,
        "shared_resources": {"policy": False}
    },
    "scenario": {
        "clusters": [5],
        "opts": [""]
    },
    "countries": ["RO"],
    "snapshots": {
        "start": "2020-12-01",
        "end": "2020-12-08"
    },
    "electricity": {
        "co2limit_enable": True,
        "co2limit": 100.0e+6,
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
        "default_cutout": "europe-2020-sarah3-era5",
        "cutouts": {
            "europe-2020-sarah3-era5": {
                "module": ["sarah", "era5"],
                "x": [-12.0, 42.0],
                "y": [33.0, 72.0],
                "dx": 0.3,
                "dy": 0.3,
                "time": ["2020", "2020"]
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

# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIOS = [
    {
        "number": "01",
        "name": "nuclear_blackout",
        "description": "Complete nuclear shutdown - all nuclear plants offline",
        "modifications": lambda cfg: (
            cfg["electricity"]["extendable_carriers"]["Generator"].remove("nuclear") 
            if "nuclear" in cfg["electricity"]["extendable_carriers"]["Generator"] else None,
            cfg.update({"electricity": {**cfg["electricity"], 
                "powerplants_filter": "(DateOut >= 2024 or DateOut != DateOut) and Fueltype != 'Nuclear'"}}),
        )[-1] or cfg
    },
    {
        "number": "02", 
        "name": "hydro_drought",
        "description": "Severe drought - hydro availability reduced to 20%",
        "modifications": lambda cfg: cfg.update({
            "renewable": {
                **cfg.get("renewable", {}),
                "hydro": {
                    "carriers": ["ror", "PHS", "hydro"],
                    "PHS_max_hours": 6,
                    "hydro_max_hours": 1.0,  # Reduced storage
                    "flatten_dispatch": False,
                    "clip_min_inflow": 0.2  # Only 20% of normal inflow
                }
            }
        }) or cfg
    },
    {
        "number": "03",
        "name": "no_wind",
        "description": "Extreme calm period - wind capacity factor at 10%",
        "modifications": lambda cfg: cfg.update({
            "renewable": {
                **cfg.get("renewable", {}),
                "onwind": {
                    "cutout": "default",
                    "capacity_per_sqkm": 0.3,  # Reduced from 3
                    "clip_p_max_pu": 0.1  # Max 10% output
                },
                "offwind-ac": {
                    **cfg.get("renewable", {}).get("offwind-ac", {}),
                    "capacity_per_sqkm": 0.2,
                    "clip_p_max_pu": 0.1
                }
            }
        }) or cfg
    },
    {
        "number": "04",
        "name": "cloudy_winter",
        "description": "Overcast conditions - solar output reduced by 70%",
        "modifications": lambda cfg: cfg.update({
            "renewable": {
                **cfg.get("renewable", {}),
                "solar": {
                    "cutout": "default",
                    "capacity_per_sqkm": 1.5,  # Reduced from 5.1
                    "clip_p_max_pu": 0.3  # Max 30% output
                }
            }
        }) or cfg
    },
    {
        "number": "05",
        "name": "gas_crisis",
        "description": "No gas imports - OCGT and CCGT unavailable",
        "modifications": lambda cfg: (
            [cfg["electricity"]["extendable_carriers"]["Generator"].remove(g) 
             for g in ["OCGT", "CCGT"] 
             if g in cfg["electricity"]["extendable_carriers"]["Generator"]],
            cfg.update({"electricity": {**cfg["electricity"],
                "gaslimit_enable": True,
                "gaslimit": 0  # Zero gas allowed
            }})
        )[-1] or cfg
    },
    {
        "number": "06",
        "name": "peak_demand",
        "description": "Extreme demand - 30% higher electricity load",
        "modifications": lambda cfg: cfg.update({
            "load": {
                "scaling_factor": 1.3,  # 30% higher demand
                "fixed_year": False
            }
        }) or cfg
    },
    {
        "number": "07",
        "name": "grid_failure",
        "description": "Major transmission failures - grid capacity at 60%",
        "modifications": lambda cfg: cfg.update({
            "lines": {
                **cfg.get("lines", {}),
                "s_max_pu": 0.4,  # Reduced from 0.7
                "max_extension": 0  # No new lines can be built
            }
        }) or cfg
    },
    {
        "number": "08",
        "name": "coal_phaseout",
        "description": "Immediate coal phase-out - all coal and lignite retired",
        "modifications": lambda cfg: cfg.update({
            "electricity": {
                **cfg["electricity"],
                "powerplants_filter": "(DateOut >= 2024 or DateOut != DateOut) and Fueltype not in ['Hard Coal', 'Lignite', 'Coal']"
            }
        }) or cfg
    },
    {
        "number": "09",
        "name": "import_isolation",
        "description": "Full autarky - no electricity imports from neighbors",
        "modifications": lambda cfg: cfg.update({
            "electricity": {
                **cfg["electricity"],
                "autarky": {
                    "enable": True,
                    "by_country": True
                }
            }
        }) or cfg
    },
    {
        "number": "10",
        "name": "combined_crisis",
        "description": "Combined crisis - Nuclear + Hydro drought + Gas crisis",
        "modifications": lambda cfg: (
            # Remove nuclear
            [cfg["electricity"]["extendable_carriers"]["Generator"].remove(g) 
             for g in ["nuclear", "OCGT", "CCGT"] 
             if g in cfg["electricity"]["extendable_carriers"]["Generator"]],
            # Add constraints
            cfg.update({
                "electricity": {
                    **cfg["electricity"],
                    "powerplants_filter": "(DateOut >= 2024 or DateOut != DateOut) and Fueltype != 'Nuclear'",
                    "gaslimit_enable": True,
                    "gaslimit": 0
                },
                "renewable": {
                    **cfg.get("renewable", {}),
                    "hydro": {
                        "carriers": ["ror", "PHS", "hydro"],
                        "PHS_max_hours": 6,
                        "hydro_max_hours": 1.0,
                        "clip_min_inflow": 0.2
                    }
                }
            })
        )[-1] or cfg
    }
]

# ============================================================================
# GENERATE CONFIG FILES
# ============================================================================

print(f"Generating {len(SCENARIOS)} adversarial scenario configs...")
print(f"Output directory: {OUTPUT_DIR}\n")

generated_files = []

for scenario in SCENARIOS:
    # Deep copy base config
    cfg = copy.deepcopy(BASE_CONFIG)
    
    # Set run name
    cfg["run"]["name"] = f"romania-adversarial-{scenario['number']}-{scenario['name']}"
    
    # Apply scenario-specific modifications
    scenario["modifications"](cfg)
    
    # Generate filename
    filename = f"romania_adversarial_{scenario['number']}_{scenario['name']}.yaml"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Add description as comment (via separate field)
    cfg["_scenario_description"] = scenario["description"]
    
    # Write YAML file
    with open(filepath, 'w') as f:
        f.write(f"# Adversarial Scenario: {scenario['description']}\n")
        f.write(f"# Run name: {cfg['run']['name']}\n\n")
        yaml.dump(cfg, f, sort_keys=False, default_flow_style=False)
    
    generated_files.append(filepath)
    print(f"  ✓ Created: {filename}")

print(f"\n{'='*60}")
print(f"Generated {len(generated_files)} adversarial scenario configs!")
print(f"{'='*60}")

# Print summary table
print("\n## Scenario Summary")
print("-" * 80)
print(f"{'#':<4} {'Name':<25} {'Description':<45}")
print("-" * 80)
for scenario in SCENARIOS:
    print(f"{scenario['number']:<4} {scenario['name']:<25} {scenario['description']:<45}")
print("-" * 80)

print("\n## To run a scenario:")
print("conda run -n pypsa snakemake -call results/{run_name}/networks/base_s_5_elec_.nc \\")
print("    --configfile config/adversarial/{config_file}.yaml")
