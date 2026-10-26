#!/bin/bash 
#SBATCH --account=mcs_prime
#SBATCH --ntasks=1
#SBATCH --job-name=model_precip_nc
#SBATCH --array=0-4
#SBATCH --time=02:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --partition=standard
#SBATCH --qos=high
#SBATCH --output=slurm/output/%j.out
#SBATCH --error=slurm/output/%j.err

source ~/miniforge3/bin/activate || exit 1
conda activate hk26_env || exit 1

python process_model_precip.py --start 2020-06-01 --end 2020-09-30 --region INDIA 

