import matplotlib.pyplot as plt
import numpy as np

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-log_file", help="log file name", type=str, default="log_cfd_simulation.txt")
parser.add_argument("-start_time", help="start time step", type=int, default=0)
parser.add_argument("-end_time", help="end time step", type=int, default=-1)
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

# Create the plot
plt.figure(figsize=(12, 8))

time_steps = np.arange(len(U0_residuals))
plt.semilogy(time_steps[args.start_time:args.end_time], U0_residuals[args.start_time:args.end_time], "o-", label="U0 (Velocity X)", linewidth=2, markersize=4)
plt.semilogy(time_steps[args.start_time:args.end_time], U1_residuals[args.start_time:args.end_time], "s-", label="U1 (Velocity Y)", linewidth=2, markersize=4)
plt.semilogy(time_steps[args.start_time:args.end_time], U2_residuals[args.start_time:args.end_time], "^-", label="U2 (Velocity Z)", linewidth=2, markersize=4)
plt.semilogy(time_steps[args.start_time:args.end_time], he_residuals[args.start_time:args.end_time], "d-", label="he (Energy)", linewidth=2, markersize=4)
plt.semilogy(time_steps[args.start_time:args.end_time], p_residuals[args.start_time:args.end_time], "p-", label="p (Pressure)", linewidth=2, markersize=4)
plt.semilogy(time_steps[args.start_time:args.end_time], nuTilda_residuals[args.start_time:args.end_time], "*-", label="nuTilda (Turbulence)", linewidth=2, markersize=4)

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
