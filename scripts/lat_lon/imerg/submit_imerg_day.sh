#!/bin/bash
#SBATCH --account=mcs_prime
#SBATCH --ntasks=1
#SBATCH --job-name=imerg_extract 
#SBATCH --array=0-12
#SBATCH --time=00:20:00
#SBATCH --mem=3G
#SBATCH --cpus-per-task=1
#SBATCH --partition=standard
#SBATCH --qos=high
#SBATCH --output=slurm/output/%j.out
#SBATCH --error=slurm/output/%j.err


echo "HOME=$HOME"
echo "USER=$(whoami)"
echo "HOST=$(hostname)"
echo "PWD=$(pwd)"


source ~/miniforge3/bin/activate || exit 1 
conda activate hk26_env || exit 1
which python

python process_imerg_day.py $SLURM_ARRAY_TASK_ID
