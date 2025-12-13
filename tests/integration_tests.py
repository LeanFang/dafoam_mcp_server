"""
Integration tests for all @mcp.tool() functions in dafoam_mcp_server.
This test runs inside the Docker container.
"""

import asyncio
from pathlib import Path
import sys
import time

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
    wing_run_cfd_simulation,
    wing_view_pressure_profile,
    wing_view_flow_field,
)


async def wait_for_run_completion(module="airfoil", timeout=600, check_interval=10):
    """
    Wait for CFD simulation or optimization to complete.

    Args:
        module: "airfoil" or "wing"
        timeout: Maximum time to wait in seconds
        check_interval: Time between status checks in seconds

    Returns:
        bool: True if completed, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = await mcp_check_run_status(module=module)
        if status == 1:
            print(f"  [{module}] Run completed")
            return True
        print(f"  [{module}] Still running... waiting {check_interval}s")
        time.sleep(check_interval)

    print(f"  [{module}] Timeout waiting for completion")
    return False


def check_files_exist(file_paths):
    """
    Check if a list of files exist.

    Args:
        file_paths: List of file paths to check

    Returns:
        bool: True if all files exist, False otherwise
    """
    all_exist = True
    for file_path in file_paths:
        if not Path(file_path).exists():
            print(f"    [FAIL] Missing: {file_path}")
            all_exist = False
        else:
            print(f"    [PASS] Found: {file_path}")
    return all_exist


def test_airfoil_generate_mesh():
    """Test airfoil_generate_mesh function."""
    print("Testing airfoil_generate_mesh...")

    try:
        result = asyncio.run(
            airfoil_generate_mesh(
                airfoil_profile="naca0012",
                mesh_cells=5000,
                y_plus=50.0,
                n_ffd_points=10,
                mach_number=0.1,
            )
        )
        print(f"Output: {result}")

        # Check for expected output files
        expected_files = [
            "../airfoils/log_mesh.txt",
            "../airfoils/plots/airfoil_mesh_overview.png",
            "../airfoils/plots/airfoil_mesh_le.png",
            "../airfoils/plots/airfoil_mesh_te.png",
            "../airfoils/plots/airfoil_mesh_all_views.html",
        ]

        if check_files_exist(expected_files):
            print("[PASS] airfoil_generate_mesh PASSED\n")
            return True
        else:
            print("[FAIL] airfoil_generate_mesh FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_airfoil_view_mesh():
    """Test airfoil_view_mesh function."""
    print("Testing airfoil_view_mesh...")

    try:
        result = asyncio.run(airfoil_view_mesh())
        print(f"Output: {result}")

        # Check for expected output file
        if check_files_exist(["../airfoils/plots/airfoil_mesh.html"]):
            print("[PASS] airfoil_view_mesh PASSED\n")
            return True
        else:
            print("[FAIL] airfoil_view_mesh FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_airfoil_run_cfd_and_views():
    """Test CFD simulation and visualization functions that depend on it."""
    print("Testing airfoil_run_cfd_simulation and related views...")

    try:
        # Start CFD simulation
        print("  Starting CFD simulation...")
        result = asyncio.run(airfoil_run_cfd_simulation())
        print(f"  Output: {result}")

        if "background" not in str(result).lower() and "started" not in str(result).lower():
            print("[FAIL] CFD simulation did not start properly\n")
            return False

        # Wait for completion
        print("  Waiting for CFD simulation to complete...")
        completed = asyncio.run(wait_for_run_completion(module="airfoil", timeout=60, check_interval=5))

        if not completed:
            print("[FAIL] CFD simulation did not complete in time\n")
            return False

        # Test visualization functions that need CFD results
        print("  Testing view_cfd_convergence...")
        conv_result = asyncio.run(view_cfd_convergence(module="airfoil"))
        print(f"    Output: {conv_result}")

        print("  Testing airfoil_view_pressure_profile...")
        pressure_result = asyncio.run(airfoil_view_pressure_profile())
        print(f"    Output: {pressure_result}")

        print("  Testing airfoil_view_flow_field...")
        flow_result = asyncio.run(airfoil_view_flow_field())
        print(f"    Output: {flow_result}")

        # Check all visualization files
        visualization_files = [
            "../airfoils/plots/airfoil_convergence.html",
            "../airfoils/plots/airfoil_pressure_profile.html",
            "../airfoils/plots/airfoil_flow_field.html",
        ]

        if check_files_exist(visualization_files):
            print("[PASS] airfoil_run_cfd_and_views PASSED\n")
            return True
        else:
            print("[FAIL] airfoil_run_cfd_and_views FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_airfoil_run_optimization_and_views():
    """Test optimization and visualization functions that depend on it."""
    print("Testing airfoil_run_optimization and related views...")

    try:
        # Clean up the run finished marker from previous CFD run
        run_finished_marker = Path("../airfoils/.dafoam_run_finished")
        if run_finished_marker.exists():
            run_finished_marker.unlink()
            print("  Cleaned up previous run marker")

        # Start optimization
        print("  Starting optimization...")
        result = asyncio.run(airfoil_run_optimization(max_opt_iters=2))
        print(f"  Output: {result}")

        if "background" not in str(result).lower() and "started" not in str(result).lower():
            print("[FAIL] Optimization did not start properly\n")
            return False

        # Wait for completion
        print("  Waiting for optimization to complete...")
        completed = asyncio.run(wait_for_run_completion(module="airfoil", timeout=1200, check_interval=10))

        if not completed:
            print("[FAIL] Optimization did not complete in time\n")
            return False

        # Test visualization function
        print("  Testing airfoil_view_optimization_history...")
        opt_result = asyncio.run(airfoil_view_optimization_history())
        print(f"    Output: {opt_result}")

        if check_files_exist(
            [
                "../airfoils/plots/airfoil_opt_hst_cd.png",
                "../airfoils/plots/airfoil_opt_hst_cl.png",
                "../airfoils/plots/airfoil_opt_hst_aoa.png",
                "../airfoils/plots/airfoil_opt_hst_shape.png",
                "../airfoils/plots/airfoil_opt_hst_optimality.png",
                "../airfoils/plots/airfoil_opt_hst_feasibility.png",
            ]
        ):
            print("[PASS] airfoil_run_optimization_and_views PASSED\n")
            return True
        else:
            print("[FAIL] airfoil_run_optimization_and_views FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_wing_generate_geometry():
    """Test wing_generate_geometry function."""
    print("Testing wing_generate_geometry...")

    try:
        result = asyncio.run(wing_generate_geometry())
        print(f"Output: {result}")

        # Check for expected output files
        expected_files = [
            "../wings/wing.iges",
            "../wings/constant/triSurface/wing_upper.stl",
            "../wings/constant/triSurface/wing_lower.stl",
            "../wings/constant/triSurface/wing_te.stl",
            "../wings/constant/triSurface/wing_tip.stl",
            "../wings/plots/wing_geometry_view_3d.png",
            "../wings/plots/wing_geometry_view_y.png",
            "../wings/plots/wing_geometry_view_x.png",
            "../wings/plots/wing_geometry_view_z.png",
            "../wings/plots/wing_geometry_all_views.html",
        ]

        if check_files_exist(expected_files):
            print("[PASS] wing_generate_geometry PASSED\n")
            return True
        else:
            print("[FAIL] wing_generate_geometry FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_wing_generate_mesh():
    """Test wing_generate_mesh function."""
    print("Testing wing_generate_mesh...")

    try:
        result = asyncio.run(wing_generate_mesh())
        print(f"Output: {result}")

        # Check for expected output files
        expected_files = [
            "../wings/log_mesh.txt",
            "../wings/plots/wing_mesh_view_3d.png",
            "../wings/plots/wing_mesh_view_y.png",
            "../wings/plots/wing_mesh_view_x.png",
            "../wings/plots/wing_mesh_view_z.png",
            "../wings/plots/wing_mesh_all_views.html",
        ]

        if check_files_exist(expected_files):
            print("[PASS] wing_generate_mesh PASSED\n")
            return True
        else:
            print("[FAIL] wing_generate_mesh FAILED\n")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}\n")
        return False


def test_wing_run_cfd_and_views():
    """Test wing CFD simulation and visualization functions that depend on it."""
    print("Testing wing_run_cfd_simulation and related views...")

    try:
        # Clean up the run finished marker from any previous run
        run_finished_marker = Path("../wings/.dafoam_run_finished")
        if run_finished_marker.exists():
            run_finished_marker.unlink()
            print("  Cleaned up previous run marker")

        # Start CFD simulation
        print("  Starting wing CFD simulation...")
        result = asyncio.run(wing_run_cfd_simulation(primal_func_std_tol=1e-2))
        print(f"  Output: {result}")

        if "background" not in str(result).lower() and "started" not in str(result).lower():
            print("[FAIL] Wing CFD simulation did not start properly\n")
            return False

        # Wait for completion
        print("  Waiting for wing CFD simulation to complete...")
        completed = asyncio.run(wait_for_run_completion(module="wing", timeout=1200, check_interval=10))

        if not completed:
            print("[FAIL] Wing CFD simulation did not complete in time\n")
            return False

        # Test visualization functions that need CFD results
        print("  Testing view_cfd_convergence for wing...")
        conv_result = asyncio.run(view_cfd_convergence(module="wing"))
        print(f"    Output: {conv_result}")

        print("  Testing wing_view_pressure_profile...")
        pressure_result = asyncio.run(wing_view_pressure_profile())
        print(f"    Output: {pressure_result}")

        print("  Testing wing_view_flow_field...")
        flow_result = asyncio.run(wing_view_flow_field())
        print(f"    Output: {flow_result}")

        # Check all visualization files
        visualization_files = [
            "../wings/plots/wing_function_cd.png",
            "../wings/plots/wing_function_cl.png",
            "../wings/plots/wing_function_cm.png",
            "../wings/plots/wing_residual_cfd.png",
            "../wings/plots/wing_pressure_profile.html",
            "../wings/plots/wing_flow_field.html",
        ]

        if check_files_exist(visualization_files):
            print("[PASS] wing_run_cfd_and_views PASSED\n")
            return True
        else:
            print("[FAIL] wing_run_cfd_and_views FAILED\n")
            return False

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
        ("airfoil_view_mesh", test_airfoil_view_mesh),
        ("airfoil_run_cfd_and_views", test_airfoil_run_cfd_and_views),
        ("airfoil_run_optimization_and_views", test_airfoil_run_optimization_and_views),
        ("wing_generate_geometry", test_wing_generate_geometry),
        ("wing_generate_mesh", test_wing_generate_mesh),
        ("wing_run_cfd_and_views", test_wing_run_cfd_and_views),
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
