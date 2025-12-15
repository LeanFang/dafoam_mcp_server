#!/bin/bash
#SBATCH -A xx-xxxxxxxxx         # project ID on Stampede3, need to change to your own
#SBATCH -J wing_opt             # job name
#SBATCH -o log-%j.txt           # output and error file name (%j expands to jobID)
#SBATCH -n 48                   # total number of mpi tasks requested
#SBATCH -N 1                    # total number of nodes
#SBATCH -p skx                  # queue (partition) skx: skylake nodes
#SBATCH -t 24:00:00             # run time (hh:mm:ss) 
#SBATCH --mail-type=ALL         # setup email alert
#SBATCH --mail-user=xxx@gmail.com

# Load the DAFoam environment. Need to change the path here
. /replace_this_to_your_absolute_dafoam_path_on_hpc/loadDAFoam.sh

# this is the script written by dafoam_mcp_server.py. No need to change anything here.
./myRun.sh