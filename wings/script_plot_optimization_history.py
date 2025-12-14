"""
Script to extract and plot optimization history from pyOptSparse .hst file
Plots: CD, CL, angle of attack, and twist variables vs major iterations

Input: OptView.hst (hardcoded)
Outputs: wing_opt_hst_cd.png, wing_opt_hst_cl.png,
         wing_opt_hst_aoa.png, wing_opt_hst_twist.png (twist angles)
"""

import logging
import shelve
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sqlitedict import SqliteDict


def read_history_file(hist_file):
    """
    Read the history file and extract all relevant data for major iterations

    Args:
        hist_file: Path to the .hst history file

    Returns:
        iterations: List of major iteration numbers
        cd_values: List of CD (drag coefficient) values
        cl_values: List of CL (lift coefficient) values
        aoa_values: List of angle of attack values (if available)
        twist_vars: Dictionary of twist variable arrays
    """

    # Try to open as classic shelve format first
    OpenMDAO = False
    try:
        db = shelve.open(hist_file, "r")
        logging.info("Opened as shelve format")
    except:
        # Try SqliteDict format
        try:
            db = SqliteDict(hist_file, "iterations")
            keys = [i for i in db.keys()]
            if keys == []:
                OpenMDAO = False
                db.close()
                db = SqliteDict(hist_file)
                logging.info("Opened as SqliteDict format")
            else:
                OpenMDAO = True
                logging.info("Opened as OpenMDAO SqliteDict format")
        except:
            raise Exception(f"Could not open history file: {hist_file}")

    iterations = []
    cd_values = []
    cl_values = []
    aoa_values = []
    twist_vars = {}  # Will store arrays for each twist variable

    cd_name = None
    cl_name = None

    if OpenMDAO:
        logging.info("OpenMDAO format not fully implemented for multiple plots")
        db.close()
        return iterations, cd_values, cl_values, aoa_values, twist_vars

    else:
        # Handle pyOptSparse format
        logging.info("Reading pyOptSparse format history file...")
        nkey = int(db["last"]) + 1

        # Read scaling information
        scaling_dict = {}
        try:
            if "varInfo" in db:
                var_info = db["varInfo"]
                for key, info in var_info.items():
                    if "scale" in info:
                        scaling_dict[key] = info["scale"]

            if "conInfo" in db:
                con_info = db["conInfo"]
                for key, info in con_info.items():
                    if "scale" in info:
                        scaling_dict[key] = info["scale"]

            if "objInfo" in db:
                obj_info = db["objInfo"]
                for key, info in obj_info.items():
                    if "scale" in info:
                        scaling_dict[key] = info["scale"]

            if len(scaling_dict) > 0:
                logging.info(f"Found scaling information for {len(scaling_dict)} variables")
        except KeyError:
            logging.info("No scaling information found in history file")

        # Check if major iteration info is stored
        stored_iters = False
        if "0" in db:
            stored_iters = "isMajor" in db["0"].keys()

        logging.info(f"File has 'isMajor' info: {stored_iters}")

        # Determine major iterations
        iter_type = np.zeros(nkey)  # 0 = skip, 1 = major, 2 = minor
        previous_iter_counter = -1

        for i in range(nkey):
            key = str(i)
            if key not in db:
                continue

            data = db[key]

            if "funcs" in data:
                if "iter" in data and data["iter"] == previous_iter_counter:
                    iter_type[i] = 0  # duplicated info
                elif not stored_iters:
                    iter_type[i] = 1  # major
                elif stored_iters and data.get("isMajor", False):
                    iter_type[i] = 1  # major
                else:
                    iter_type[i] = 2  # minor

                if "iter" in data:
                    previous_iter_counter = data["iter"]
            else:
                iter_type[i] = 0

        logging.info(f"Found {int(np.sum(iter_type == 1))} major iterations")

        # Extract data for major iterations
        major_iter = 0
        for i in range(nkey):
            if iter_type[i] == 1:  # Only major iterations
                key = str(i)
                if key not in db:
                    continue

                data = db[key]

                # Extract functions (CD, CL)
                if "funcs" in data:
                    funcs = data["funcs"]

                    # Find CD
                    if cd_name is None:
                        for func_key in funcs.keys():
                            if "cd" in func_key.lower() and "drag" not in func_key.lower():
                                cd_name = func_key
                                logging.info(f"Found CD: {cd_name}")
                                break

                    # Find CL
                    if cl_name is None:
                        for func_key in funcs.keys():
                            if "cl" in func_key.lower() and "lift" not in func_key.lower():
                                cl_name = func_key
                                logging.info(f"Found CL: {cl_name}")
                                break

                    # Extract CD value and unscale
                    if cd_name and cd_name in funcs:
                        val = funcs[cd_name]
                        if isinstance(val, (list, np.ndarray)):
                            val = val[0] if len(val) > 0 else val
                        val = float(val)
                        # Unscale if scaling info available
                        if cd_name in scaling_dict:
                            val = val / scaling_dict[cd_name]
                        cd_values.append(val)
                    else:
                        cd_values.append(np.nan)

                    # Extract CL value and unscale
                    if cl_name and cl_name in funcs:
                        val = funcs[cl_name]
                        if isinstance(val, (list, np.ndarray)):
                            val = val[0] if len(val) > 0 else val
                        val = float(val)
                        # Unscale if scaling info available
                        if cl_name in scaling_dict:
                            val = val / scaling_dict[cl_name]
                        cl_values.append(val)
                    else:
                        cl_values.append(np.nan)

                # Extract design variables (twist variables and patchV which is angle of attack)
                if "xuser" in data:
                    xuser = data["xuser"]

                    # Extract twist variables and angle of attack (patchV)
                    for var_key in xuser.keys():
                        if "twist" in var_key.lower() or "dvs" in var_key.lower():
                            val = xuser[var_key]
                            if isinstance(val, (list, np.ndarray)):
                                val = np.array(val).flatten()
                            else:
                                val = np.array([val])

                            # Unscale if scaling info available (from pyOptSparse)
                            if var_key in scaling_dict:
                                scale = scaling_dict[var_key]
                                if isinstance(scale, (list, np.ndarray)):
                                    scale = np.array(scale).flatten()
                                val = val / scale

                            # Apply problem-specific unscaling
                            # patchV: multiply by 10 to get physical values
                            if "patchv" in var_key.lower():
                                val = val * 10.0
                                # Extract only the second component (index 1) as angle of attack
                                if len(val) > 1:
                                    aoa_values.append(float(val[1]))
                                else:
                                    aoa_values.append(np.nan)
                                # Don't add patchV to twist_vars, only extract AOA
                                continue
                            # twist: multiply by 10 to get physical values (degrees)
                            elif "twist" in var_key.lower():
                                val = val * 10.0

                            if var_key not in twist_vars:
                                twist_vars[var_key] = []
                                logging.info(f"Found twist variable: {var_key} (length: {len(val)})")

                            twist_vars[var_key].append(val)

                iterations.append(major_iter)
                major_iter += 1

    db.close()

    if len(iterations) == 0:
        raise Exception("No major iterations found in history file")

    # Convert twist_vars lists to arrays
    for key in twist_vars:
        twist_vars[key] = np.array(twist_vars[key])

    return iterations, cd_values, cl_values, aoa_values, twist_vars


def plot_all_figures(iterations, cd_values, cl_values, aoa_values, twist_vars):
    """
    Create and save separate plots for: CD, CL, angle of attack, and each twist variable

    Args:
        iterations: List of iteration numbers
        cd_values: List of CD values
        cl_values: List of CL values
        aoa_values: List of angle of attack values
        twist_vars: Dictionary of twist variable arrays
    """

    # Plot 1: CD vs iteration
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, cd_values, "b-o", linewidth=2, markersize=6)
    ax.set_xlabel("Major Iteration", fontsize=16)
    ax.set_ylabel("CD (Drag Coefficient)", fontsize=16)
    ax.set_title("Drag Coefficient History", fontsize=18, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="both", which="major", labelsize=14)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    # Annotate final value
    final_cd = cd_values[-1]
    plt.annotate(
        f"Final: {final_cd:.7f}",
        xy=(iterations[-1], final_cd),
        xytext=(-80, 30),
        textcoords="offset points",
        fontsize=16,
        arrowprops=dict(arrowstyle="->", lw=2, color="black"),
    )
    # Annotate initial value
    init_cd = cd_values[0]
    plt.annotate(
        f"Init: {init_cd:.7f}",
        xy=(iterations[0], init_cd),
        xytext=(-80, 30),
        textcoords="offset points",
        fontsize=16,
        arrowprops=dict(arrowstyle="->", lw=2, color="black"),
    )
    plt.tight_layout()
    output_file = "plots/wing_opt_hst_cd.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logging.info(f"Saved: {output_file}")
    plt.close()

    # Plot 2: CL vs iteration
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, cl_values, "r-o", linewidth=2, markersize=6)
    ax.set_xlabel("Major Iteration", fontsize=16)
    ax.set_ylabel("CL (Lift Coefficient)", fontsize=16)
    ax.set_title("Lift Coefficient History", fontsize=18, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="both", which="major", labelsize=14)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    # Annotate final value
    final_cl = cl_values[-1]
    plt.annotate(
        f"Final: {final_cl:.6f}",
        xy=(iterations[-1], final_cl),
        xytext=(-80, 30),
        textcoords="offset points",
        fontsize=16,
        arrowprops=dict(arrowstyle="->", lw=2, color="black"),
    )
    # Annotate initial value
    init_cl = cl_values[0]
    plt.annotate(
        f"Init: {init_cl:.6f}",
        xy=(iterations[0], init_cl),
        xytext=(-80, 30),
        textcoords="offset points",
        fontsize=16,
        arrowprops=dict(arrowstyle="->", lw=2, color="black"),
    )
    plt.tight_layout()
    output_file = "plots/wing_opt_hst_cl.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logging.info(f"Saved: {output_file}")
    plt.close()

    # Plot 3: Angle of attack vs iteration (from patchV[1])
    if len(aoa_values) > 0 and not all(np.isnan(aoa_values)):
        fig, ax = plt.subplots(figsize=(10, 6))
        aoa_plot = np.array(aoa_values)

        ax.plot(iterations, aoa_plot, "g-o", linewidth=2, markersize=6)
        ax.set_xlabel("Major Iteration", fontsize=16)
        ax.set_ylabel("Angle of Attack (degrees)", fontsize=16)
        ax.set_title("Angle of Attack History", fontsize=18, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="both", which="major", labelsize=14)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        # Annotate final value
        final_aoa = aoa_plot[-1]
        plt.annotate(
            f"Final: {final_aoa:.5f}",
            xy=(iterations[-1], final_aoa),
            xytext=(-80, 30),
            textcoords="offset points",
            fontsize=16,
            arrowprops=dict(arrowstyle="->", lw=2, color="black"),
        )
        # Annotate init value
        init_aoa = aoa_plot[0]
        plt.annotate(
            f"Init: {init_aoa:.5f}",
            xy=(iterations[0], init_aoa),
            xytext=(-80, 30),
            textcoords="offset points",
            fontsize=16,
            arrowprops=dict(arrowstyle="->", lw=2, color="black"),
        )
        plt.tight_layout()
        output_file = "plots/wing_opt_hst_aoa.png"
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        logging.info(f"Saved: {output_file}")
        plt.close()
    else:
        logging.info("No angle of attack data found")

    # Plot 4+: Twist variables - each gets its own separate plot
    if len(twist_vars) > 0:
        for var_idx, (var_name, var_data) in enumerate(twist_vars.items()):
            fig, ax = plt.subplots(figsize=(10, 6))

            # var_data is shape (n_iterations, n_variables)
            n_iters, n_vars = var_data.shape

            # Plot each component with legend
            if n_vars <= 20:
                # Plot all components if not too many
                for i in range(n_vars):
                    ax.plot(
                        iterations,
                        var_data[:, i],
                        "-o",
                        linewidth=1.5,
                        markersize=4,
                        label=f"Component {i}",
                        alpha=0.7,
                    )
                ax.legend(ncol=2, fontsize=10, framealpha=0.9)
            else:
                # Plot min, max, and mean if too many components
                mean_vals = np.mean(var_data, axis=1)
                min_vals = np.min(var_data, axis=1)
                max_vals = np.max(var_data, axis=1)

                ax.plot(
                    iterations,
                    mean_vals,
                    "b-o",
                    linewidth=2,
                    markersize=4,
                    label="Mean",
                )
                ax.fill_between(iterations, min_vals, max_vals, alpha=0.3, label="Min-Max Range")
                ax.legend(fontsize=12, framealpha=0.9)

            ax.set_xlabel("Major Iteration", fontsize=16)
            ax.set_ylabel("Twist Angle (degrees)", fontsize=16)
            ax.set_title(
                f"Wing Twist Angle History (n={n_vars} spanwise sections)",
                fontsize=18,
                fontweight="bold",
            )
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="both", which="major", labelsize=14)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            plt.tight_layout()

            output_file = "plots/wing_opt_hst_twist.png"

            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logging.info(f"Saved: {output_file}")
            plt.close()
            # force to plot only the first twist variable
            break
    else:
        logging.info("No twist variables found")

    # plot optimality and feasibility
    with open("opt_IPOPT.txt", "r") as f:
        lines = f.readlines()

    opt_iter = []
    optimality = []
    feasibility = []
    for line in lines:
        try:
            iterI = int(line.split()[0])
            opt_iter.append(iterI)
            optimality.append(float(line.split()[3]))
            feasibility.append(float(line.split()[2]))
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(10, 6))
    # Replace zeros with a small positive value for log plotting
    optimality_plot = np.array(optimality)
    floor_value = 1e-16
    optimality_plot[optimality_plot <= 0] = floor_value
    ax.semilogy(opt_iter, optimality_plot, "-ko", linewidth=2, markersize=6)
    ax.set_xlabel("Major Iteration", fontsize=16)
    ax.set_ylabel("Optimality", fontsize=16)
    ax.set_title("Optimality History", fontsize=18, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="both", which="major", labelsize=14)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    plt.tight_layout()
    output_file = "plots/wing_opt_hst_optimality.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logging.info(f"Saved: {output_file}")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 6))
    # Replace zeros with a small positive value for log plotting
    feasibility_plot = np.array(feasibility)
    floor_value = 1e-16
    feasibility_plot[feasibility_plot <= 0] = floor_value
    ax.semilogy(opt_iter, feasibility_plot, "-rs", linewidth=2, markersize=6)
    ax.set_xlabel("Major Iteration", fontsize=16)
    ax.set_ylabel("Feasibility", fontsize=16)
    ax.set_title("Feasibility History", fontsize=18, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="both", which="major", labelsize=14)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    plt.tight_layout()
    output_file = "plots/wing_opt_hst_feasibility.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logging.info(f"Saved: {output_file}")
    plt.close()

    # Print summary statistics
    logging.info(f"\n{'='*60}")
    logging.info("OPTIMIZATION SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Number of major iterations: {len(iterations)}")

    if len(cd_values) > 0:
        logging.info(f"\nCD (Drag Coefficient):")
        logging.info(f"  Initial: {cd_values[0]:.6e}")
        logging.info(f"  Final:   {cd_values[-1]:.6e}")
        if cd_values[0] != 0:
            change_pct = ((cd_values[-1] - cd_values[0]) / cd_values[0]) * 100
            logging.info(f"  Change:  {change_pct:.2f}%")

    if len(cl_values) > 0:
        logging.info(f"\nCL (Lift Coefficient):")
        logging.info(f"  Initial: {cl_values[0]:.6e}")
        logging.info(f"  Final:   {cl_values[-1]:.6e}")
        if cl_values[0] != 0:
            change_pct = ((cl_values[-1] - cl_values[0]) / cl_values[0]) * 100
            logging.info(f"  Change:  {change_pct:.2f}%")

    if len(aoa_values) > 0 and not all(np.isnan(aoa_values)):
        logging.info(f"\nAngle of Attack:")
        logging.info(f"  Initial: {aoa_values[0]:.6f}")
        logging.info(f"  Final:   {aoa_values[-1]:.6f}")

    logging.info(f"{'='*60}\n")


def main():
    """Main function to extract and plot optimization history"""

    hist_file = "OptView.hst"

    logging.info(f"Reading history file: {hist_file}\n")

    # Extract data
    iterations, cd_values, cl_values, aoa_values, twist_vars = read_history_file(hist_file)

    # Create plots
    plot_all_figures(iterations, cd_values, cl_values, aoa_values, twist_vars)


if __name__ == "__main__":
    main()
