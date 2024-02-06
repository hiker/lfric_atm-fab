#!/bin/bash

# get the current lfric revision from the repo mirror
rev=$(svn info file:///g/data/ki32/mosrs/lfric/LFRic/trunk | grep Revision | sed 's/.* //g')
echo $rev > /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab/lfric_revision

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-lfric-fab

# grab the lfric sources
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/grab_lfric.py

# build lfric_atm
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/atm.py

#rev='46556'

cp lfric_source_${rev}/source/lfric/lfric_atm/example/configuration.nml /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab
cp lfric_source_${rev}/source/lfric/lfric_atm/example/iodef.xml /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab
cp lfric_source_${rev}/source/lfric/lfric_atm/example/mesh_BiP4x4-2500x2500.nc /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab

cp atm_ifort_1stage/lfric_atm.exe /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN/0/bom/ngm/lfric/lfric_atm-fab
