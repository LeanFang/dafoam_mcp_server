import matplotlib.pyplot as plt
import numpy as np

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-log_file", help="log file name", type=str, default="log_cfd_simulation.txt")
args = parser.parse_args()

# Read the log file
with open(args.log_file, "r") as f:
    lines = f.readlines()

# Initialize lists to store data
time_steps = []
U0_residuals = []
U1_residuals = []
U2_residuals = []
he_residuals = []
p_residuals = []
nuTilda_residuals = []

# Parse the log file for residual data
for i, line in enumerate(lines):
    if (
        "Time = " in line
        and "ExecutionTime" not in line
        and "Time = 0" not in line
        and "Minimal residual" not in lines[i + 1]
    ):
        time_steps.append(float(line.split()[2]))
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

# Create the plot
plt.figure(figsize=(12, 8))

plt.semilogy(time_steps, U0_residuals, "o-", label="U0 (Velocity X)", linewidth=2, markersize=4)
plt.semilogy(time_steps, U1_residuals, "s-", label="U1 (Velocity Y)", linewidth=2, markersize=4)
plt.semilogy(time_steps, U2_residuals, "^-", label="U2 (Velocity Z)", linewidth=2, markersize=4)
plt.semilogy(time_steps, he_residuals, "d-", label="he (Energy)", linewidth=2, markersize=4)
plt.semilogy(time_steps, p_residuals, "p-", label="p (Pressure)", linewidth=2, markersize=4)
plt.semilogy(time_steps, nuTilda_residuals, "*-", label="nuTilda (Turbulence)", linewidth=2, markersize=4)

# Add reference line for convergence tolerance
plt.xlabel("Iteration", fontsize=20, fontweight="bold")
plt.ylabel("Residual", fontsize=20, fontweight="bold")
plt.title("CFD Residual Convergence History", fontsize=20, fontweight="bold")
plt.legend(loc="best", fontsize=16, frameon=False)
plt.grid(True, which="both", linestyle=":", alpha=0.6)
plt.tick_params(axis="both", which="major", labelsize=20)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig('image_airfoil_residual.png', dpi=200)
