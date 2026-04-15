#!/usr/bin/env python
"""Quick validation test for 2023 cutout support implementation."""
from __future__ import annotations

import sys
from pathlib import Path

# Add scenario_manager to path for imports
scenario_manager_path = Path(__file__).resolve().parent / "1_piele_dashboard"
sys.path.insert(0, str(scenario_manager_path))

from scenario_manager.types import ScenarioInputs, StressParams
from scenario_manager.config_builder import _apply_cutout_to_config


def test_cutout_validation():
    """Test cutout year validation."""
    print("=" * 60)
    print("TEST 1: Cutout Year Validation")
    print("=" * 60)
    
    # Test valid years
    valid_years = ["2020", "2023"]
    for year in valid_years:
        cfg = {"atlite": {"cutouts": {
            "europe-2020-sarah3-era5": {},
            "europe-2023-sarah3-era5": {}
        }}}
        try:
            _apply_cutout_to_config(cfg, year)
            print(f"✓ Year {year}: Valid")
            assert cfg["atlite"]["default_cutout"] == f"europe-{year}-sarah3-era5"
            print(f"  → Cutout set to: {cfg['atlite']['default_cutout']}")
        except Exception as e:
            print(f"✗ Year {year}: {e}")
            return False
    
    # Test invalid year
    print("\nTesting invalid year (2025)...")
    cfg = {"atlite": {"cutouts": {}}}
    try:
        _apply_cutout_to_config(cfg, "2025")
        print("✗ Should have raised ValueError for 2025")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    return True


def test_cutout_definition_validation():
    """Test that cutout definitions are required."""
    print("\n" + "=" * 60)
    print("TEST 2: Cutout Definition Validation")
    print("=" * 60)
    
    # Test missing cutout definition
    cfg = {"atlite": {"cutouts": {}}}  # No definitions
    try:
        _apply_cutout_to_config(cfg, "2020")
        print("✗ Should have raised ValueError for missing cutout definition")
        return False
    except ValueError as e:
        print(f"✓ Correctly detected missing definition: {e}")
    
    return True


def test_date_validation():
    """Test snapshot date validation against cutout year."""
    print("\n" + "=" * 60)
    print("TEST 3: Snapshot Date Validation")
    print("=" * 60)
    
    # Test valid date-year matching
    cfg = {
        "atlite": {
            "cutouts": {
                "europe-2020-sarah3-era5": {},
                "europe-2023-sarah3-era5": {}
            }
        },
        "run": {
            "snapshots": {
                "start": "2020-12-01",
                "end": "2020-12-08"
            }
        }
    }
    
    try:
        _apply_cutout_to_config(cfg, "2020")
        print("✓ 2020 year with 2020-MM-DD dates: Valid")
    except Exception as e:
        print(f"✗ Should have accepted matching dates: {e}")
        return False
    
    # Test invalid date-year mismatch
    cfg["run"]["snapshots"] = {
        "start": "2023-01-15",
        "end": "2023-01-22"
    }
    
    try:
        _apply_cutout_to_config(cfg, "2020")
        print("✗ Should have rejected 2023 dates with 2020 cutout")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected mismatch: {str(e)[:70]}...")
    
    # Test valid 2023 with 2023 dates
    cfg["run"]["snapshots"] = {
        "start": "2023-01-15",
        "end": "2023-01-22"
    }
    
    try:
        _apply_cutout_to_config(cfg, "2023")
        print("✓ 2023 year with 2023-MM-DD dates: Valid")
    except Exception as e:
        print(f"✗ Should have accepted matching dates: {e}")
        return False
    
    return True


def test_scenario_inputs_creation():
    """Test ScenarioInputs with cutout_year field."""
    print("\n" + "=" * 60)
    print("TEST 4: ScenarioInputs Data Type")
    print("=" * 60)
    
    try:
        # Test with 2020 (default)
        inputs_2020 = ScenarioInputs(
            run_mode="paired",
            output_name="test-2020",
            scenario_slug="test",
            country="RO",
            countries=["RO"],
            snapshot_start="2020-12-01",
            snapshot_end="2020-12-08",
            clusters=10,
            solver_name="highs",
            solver_options="highs-simplex",
        )
        print(f"✓ Created ScenarioInputs with default cutout_year: {inputs_2020.cutout_year}")
        assert inputs_2020.cutout_year == "2020"
        
        # Test with 2023
        inputs_2023 = ScenarioInputs(
            run_mode="paired",
            output_name="test-2023",
            scenario_slug="test",
            country="RO",
            countries=["RO"],
            snapshot_start="2023-01-15",
            snapshot_end="2023-01-22",
            clusters=10,
            solver_name="highs",
            solver_options="highs-simplex",
            cutout_year="2023",
        )
        print(f"✓ Created ScenarioInputs with explicit cutout_year: {inputs_2023.cutout_year}")
        assert inputs_2023.cutout_year == "2023"
        
    except Exception as e:
        print(f"✗ Failed to create ScenarioInputs: {e}")
        return False
    
    return True


def main():
    """Run all validation tests."""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║  2023 Cutout Support - Implementation Validation Tests  ║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝\n")
    
    tests = [
        ("Cutout Year Validation", test_cutout_validation),
        ("Cutout Definition Validation", test_cutout_definition_validation),
        ("Date Validation", test_date_validation),
        ("ScenarioInputs Data Type", test_scenario_inputs_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All validation tests passed! Implementation is ready.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
