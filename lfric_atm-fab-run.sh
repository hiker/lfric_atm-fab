#!/bin/bash

set -eu
set -o pipefail

# print out current directory
echo 'current dir'
echo $PWD
export FAB_WORKSPACE=/scratch/hc46/hc46_gitlab/lfric_fab

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-fab-new-framework

# print out revisions
export lfric_core_rev=$(tac "lfric_core_revision")
echo "lfric_core_revison = ${lfric_core_rev}"

export lfric_apps_rev=$(tac "lfric_apps_revision")
echo "lfric_apps_revison = ${lfric_apps_rev}"

# run gungho_model
echo "Start running gungho_model"
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/apps/applications/gungho_model/example
echo 'current dir'
echo $PWD
imagerun mpirun -np 6 $FAB_WORKSPACE/gungho_model-ifort/gungho_model configuration.nml
echo "Finished running gungho_model"

# run lfric_atm
echo "Start running lfric_atm"
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/apps/applications/lfric_atm/example
echo 'current dir'
echo $PWD
imagerun mpirun -np 1 $FAB_WORKSPACE/lfric_atm-ifort/lfric_atm configuration.nml
echo "Finished running lfric_atm"

echo "Finished all runs"
