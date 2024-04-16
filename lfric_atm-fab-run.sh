#!/bin/bash

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

export BIN_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/gungho_model-ifort
echo "bin_dir = ${BIN_DIR}"

export CONFIG_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/lfric_source_${lfric_core_rev}/source/lfric_apps/application/gungho_model/example/
echo "config_dir = ${CONFIG_DIR}"

imagerun mpirun -np 4 $BIN_DIR/gungho_model $CONFIG_DIR/configuration.nml

echo "Finished running gungho_model"

# run lfric_atm
echo "Start running lfric_atm"

export BIN_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/lfric_atm-ifort
echo "bin_dir = ${BIN_DIR}"

export CONFIG_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/lfric_source_${lfric_core_rev}/source/lfric_apps/application/lfric_atm/example/
echo "config_dir = ${CONFIG_DIR}"

imagerun mpirun -np 1 $BIN_DIR/lfric_atm $CONFIG_DIR/configuration.nml

echo "Finished running lfric_atm"

echo "Finished all runs"
