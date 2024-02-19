#!/bin/bash

BIN_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/atm_ifort_1stage
echo $BIN_DIR

rev=$(rev < "lfric_revision")
echo $rev

CONFIG_DIR=/scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/lfric_source_${rev}/source/lfric/lfric_atm/example/
echo $CONFIG_DIR

module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-lfric-fab

cd example
imagerun mpirun -np 1 ../lfric_atm.exe configuration.nml
