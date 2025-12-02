import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-log_file", help="log file name", type=str, default="log_cfd_simulation.txt")
parser.add_argument("-start_time_cfd", help="start time step for cfd", type=int, default=0)
parser.add_argument("-end_time_cfd", help="end time step for cfd", type=int, default=-1)
parser.add_argument("-start_time_adjoint", help="start time step for adjoint", type=int, default=0)
parser.add_argument("-end_time_adjoint", help="end time step for adjoint", type=int, default=-1)
args = parser.parse_args()

# Read the log file
with open(args.log_file, "r") as f:
    lines = f.readlines()

# Initialize lists to store data
U0_residuals = []
U1_residuals = []
U2_residuals = []
he_residuals = []
p_residuals = []
nuTilda_residuals = []
adjoint_residuals = []

# Parse the log file for residual data
for i, line in enumerate(lines):
    if "U0 initRes:" in line:
        U0_residuals.append(float(line.split()[2]))
    if "U1 initRes:" in line:
        U1_residuals.append(float(line.split()[2]))
    if "U2 initRes:" in line:
        U2_residuals.append(float(line.split()[2]))
    if "he initRes:" in line:
        he_residuals.append(float(line.split()[2]))
    if "p initRes:" in line:
        p_residuals.append(float(line.split()[2]))
    if "nuTilda initRes:" in line:
        nuTilda_residuals.append(float(line.split()[2]))
    if "KSP Residual norm " in line:
        adjoint_residuals.append(float(line.split()[6]))

# Create the plot
plt.figure(figsize=(12, 8))

# make sure all variables have the same size
n_steps = len(nuTilda_residuals)
time_steps = np.arange(n_steps)
U0_residuals = U0_residuals[0:n_steps]
U1_residuals = U1_residuals[0:n_steps]
U2_residuals = U2_residuals[0:n_steps]
he_residuals = he_residuals[0:n_steps]
p_residuals = p_residuals[0:n_steps]
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    U0_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="U0 (Velocity X)",
    linewidth=2,
    markersize=4,
)
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    U1_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="U1 (Velocity Y)",
    linewidth=2,
    markersize=4,
)
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    U2_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="U2 (Velocity Z)",
    linewidth=2,
    markersize=4,
)
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    he_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="he (Energy)",
    linewidth=2,
    markersize=4,
)
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    p_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="p (Pressure)",
    linewidth=2,
    markersize=4,
)
plt.semilogy(
    time_steps[args.start_time_cfd : args.end_time_cfd],
    nuTilda_residuals[args.start_time_cfd : args.end_time_cfd],
    "-",
    label="nuTilda (Turbulence)",
    linewidth=2,
    markersize=4,
)

# Add reference line for convergence tolerance
plt.xlabel("Iteration", fontsize=20, fontweight="bold")
plt.ylabel("Flow Residual", fontsize=20, fontweight="bold")
plt.title("CFD Residual Convergence History (printed every 10 steps)", fontsize=20, fontweight="bold")
plt.legend(loc="best", fontsize=16, frameon=False)
plt.grid(True, which="both", linestyle=":", alpha=0.6)
plt.tick_params(axis="both", which="major", labelsize=20)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("plots/airfoil_residual_cfd.png", dpi=200)
plt.close()

if len(adjoint_residuals) != 0:
    time_steps = np.arange(len(adjoint_residuals))
    plt.figure(figsize=(12, 8))
    plt.semilogy(
        time_steps[args.start_time_adjoint : args.end_time_adjoint],
        adjoint_residuals[args.start_time_adjoint : args.end_time_adjoint],
        "-",
        label="adjoint",
        linewidth=2,
        markersize=4,
    )
    # Add reference line for convergence tolerance
    plt.xlabel("Iteration", fontsize=20, fontweight="bold")
    plt.ylabel("Adjoint Residual", fontsize=20, fontweight="bold")
    plt.title("Adjoint Residual Convergence History (printed every 10 steps)", fontsize=20, fontweight="bold")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.tick_params(axis="both", which="major", labelsize=20)
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig("plots/airfoil_residual_adjoint.png", dpi=200)
    plt.close()
