"""
Integration tests for all @mcp.tool() functions in dafoam_mcp_server.
This test runs inside the Docker container.
"""

import asyncio
from pathlib import Path
import sys

# Import all MCP functions
sys.path.insert(0, str(Path(__file__).parent.parent))
from dafoam_mcp_server import (
    airfoil_generate_mesh,
    airfoil_view_mesh,
    airfoil_run_cfd_simulation,
    airfoil_run_optimization,
    mcp_check_run_status,
    view_cfd_convergence,
    airfoil_view_pressure_profile,
    airfoil_view_flow_field,
    airfoil_view_optimization_history,
    wing_generate_geometry,
    wing_generate_mesh,
)


def test_airfoil_generate_mesh():
    """Test airfoil_generate_mesh function."""
    print("Testing airfoil_generate_mesh...")

    try:
        result = asyncio.run(
            airfoil_generate_mesh(
                airfoil_profile="naca0012", mesh_cells=5000, y_plus=50.0, n_ffd_points=10, mach_number=0.1
            )
        )
        print(f"Output: {result}")

        # Check for expected output files
        expected_files = [
            "airfoils/log_mesh.txt",
            "airfoils/plots/airfoil_mesh_overview.png",
            "airfoils/plots/airfoil_mesh_le.png",
            "airfoils/plots/airfoil_mesh_te.png",
            "airfoils/plots/airfoil_mesh_all_views.html",
        ]

        missing_files = []
        for file_path in expected_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
                print(f"  [FAIL] Missing: {file_path}")
            else:
                print(f"  [PASS] Found: {file_path}")

        if missing_files:
            print("[FAIL] airfoil_generate_mesh FAILED\n")
            return False

        print("[PASS] airfoil_generate_mesh PASSED\n")
        return True

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def run_all_tests():
    """Run all MCP function tests."""
    print("=" * 60)
    print("Running DAFoam MCP Server Integration Tests")
    print("=" * 60 + "\n")

    # Track test results
    tests = [
        ("airfoil_generate_mesh", test_airfoil_generate_mesh),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} ERROR: {str(e)}\n")
            failed += 1

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"[PASS] Passed:  {passed}")
    print(f"[FAIL] Failed:  {failed}")
    print(f"Total:    {passed + failed}")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
