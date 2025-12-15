#!/bin/bash
#SBATCH --time=1:00:00               # walltime limit (HH:MM:SS)
#SBATCH --nodes=1                    # number of nodes
#SBATCH --ntasks-per-node=36         # core(s)(CPU cores) per node 
#SBATCH --job-name="my_job"          # job name
#SBATCH --output="log-%j.txt"        # job standard output file (%j replaced by job id)        
#SBATCH --constraint=intel           # intel nodes

# Load the DAFoam environment. Need to change the path here
. /replace_this_to_your_absolute_dafoam_path_on_hpc/loadDAFoam.sh

# this is the script written by dafoam_mcp_server.py. No need to change anything here.
./myRun.sh
