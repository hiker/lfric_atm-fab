#!/bin/bash

set -eu
set -o pipefail

# print out current directory
echo 'current dir'
echo $PWD

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-fab-new-framework

# print out revisions
export lfric_core_rev=$(rev < "lfric_core_revision")
echo "lfric_core_revison = ${lfric_core_rev}"

export lfric_apps_rev=$(rev < "lfric_apps_revision")
echo "lfric_apps_revison = ${lfric_apps_rev}"

# run gungho_model
echo "Start running gungho_model"
cd gungho_model_example
imagerun mpirun -np 4 ../gungho_model configuration.nml

echo "Finished running gungho_model"

# run lfric_atm
echo "Start running lfric_atm"
cd lfric_atm_example
imagerun mpirun -np 1 ../lfric_atm configuration.nml

echo "Finished running lfric_atm"

echo "Finished all runs"
