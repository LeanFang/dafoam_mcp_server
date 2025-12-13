import matplotlib

matplotlib.use("Agg")
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
CD = []
CL = []
CM = []

# Parse the log file for residual data
for i, line in enumerate(lines):
    if "CD:" in line:
        CD.append(float(line.split()[1]))
    if "CL:" in line:
        CL.append(float(line.split()[1]))
    if "CM:" in line:
        CM.append(float(line.split()[1]))

# Create the plot CD
plt.figure(figsize=(12, 8))
time_size = len(CM)
time_steps = np.arange(time_size)
CD = CD[0:time_size]
CL = CL[0:time_size]
CM = CM[0:time_size]
plt.plot(
    time_steps[args.start_time : args.end_time],
    CD[args.start_time : args.end_time],
    "-",
    label="CD",
    linewidth=2,
    markersize=4,
)
# Add reference line for convergence tolerance
plt.xlabel("Iteration", fontsize=20, fontweight="bold")
plt.ylabel("CD", fontsize=20, fontweight="bold")
plt.title("CD Convergence History (printed every 10 steps)", fontsize=20, fontweight="bold")
plt.grid(True, which="both", linestyle=":", alpha=0.6)
plt.tick_params(axis="both", which="major", labelsize=20)
plt.ylim(CD[-1] * 0.5, CD[-1] * 2)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
# Annotate final value
final_cd = CD[-1]
plt.annotate(
    f"Final: {final_cd:.7f}",
    xy=(time_steps[-1], final_cd),
    xytext=(-80, 30),
    textcoords="offset points",
    fontsize=16,
    arrowprops=dict(arrowstyle="->", lw=2, color="black"),
)
plt.tight_layout()
plt.savefig("plots/wing_function_cd.png", dpi=200)
plt.close()

# Create the plot CL
plt.figure(figsize=(12, 8))
plt.plot(
    time_steps[args.start_time : args.end_time],
    CL[args.start_time : args.end_time],
    "-",
    label="CL",
    linewidth=2,
    markersize=4,
)
# Add reference line for convergence tolerance
plt.xlabel("Iteration", fontsize=20, fontweight="bold")
plt.ylabel("CL", fontsize=20, fontweight="bold")
plt.title("CL Convergence History (printed every 10 steps)", fontsize=20, fontweight="bold")
plt.grid(True, which="both", linestyle=":", alpha=0.6)
plt.tick_params(axis="both", which="major", labelsize=20)
plt.ylim(CL[-1] * 0.5, CL[-1] * 2)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
# Annotate final value
final_cl = CL[-1]
plt.annotate(
    f"Final: {final_cl:.6f}",
    xy=(time_steps[-1], final_cl),
    xytext=(-80, 30),
    textcoords="offset points",
    fontsize=16,
    arrowprops=dict(arrowstyle="->", lw=2, color="black"),
)
plt.tight_layout()
plt.savefig("plots/wing_function_cl.png", dpi=200)
plt.close()

# Create the plot CM
plt.figure(figsize=(12, 8))
plt.plot(
    time_steps[args.start_time : args.end_time],
    CM[args.start_time : args.end_time],
    "-",
    label="CM",
    linewidth=2,
    markersize=4,
)
# Add reference line for convergence tolerance
plt.xlabel("Iteration", fontsize=20, fontweight="bold")
plt.ylabel("CM", fontsize=20, fontweight="bold")
plt.title("CM Convergence History (printed every 10 steps)", fontsize=20, fontweight="bold")
plt.grid(True, which="both", linestyle=":", alpha=0.6)
plt.tick_params(axis="both", which="major", labelsize=20)
plt.ylim(CM[-1] * 0.5, CM[-1] * 2)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
# Annotate final value
final_cm = CM[-1]
plt.annotate(
    f"Final: {final_cm:.8f}",
    xy=(time_steps[-1], final_cm),
    xytext=(-80, 30),
    textcoords="offset points",
    fontsize=16,
    arrowprops=dict(arrowstyle="->", lw=2, color="black"),
)
plt.tight_layout()
plt.savefig("plots/wing_function_cm.png", dpi=200)
plt.close()
