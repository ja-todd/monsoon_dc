#!/bin/bash 
mkdir -p slurm/output 
sbatch "$@" submit_imerg_day.sh
