#!/bin/bash
slurm_jobid_prpt () { echo ""; }
export -f slurm_jobid_prpt
module restore data_product
alias queue="squeue -u aashrayc --format='%.18i %.9P %.100j %.8u %.8T %.10M %.9l %.6D %R'"
