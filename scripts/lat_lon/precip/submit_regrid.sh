#!/bin/bash 
#SBATCH --account=mcs_prime
#SBATCH --ntasks=1
#SBATCH --job-name=regrid_model_precip
#SBATCH --array=0-3
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --partition=standard
#SBATCH --qos=high
#SBATCH --output=slurm/output/%j.out
#SBATCH --error=slurm/output/%j.err

source ~/miniforge3/bin/activate || exit 1
conda activate hk26_env || exit 1

python regrid_precip_data.py $SLURM_ARRAY_TASK_ID

