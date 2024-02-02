#!/bin/bash

# get the current lfric revision from the repo mirror
rev=$(svn info file:///g/data/ki32/mosrs/lfric/LFRic/trunk | grep Revision | sed 's/.* //g')
echo "revision:"
echo $rev

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-lfric-fab

# grab the lfric sources
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/grab_lfric.py $rev

# build lfric_atm
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/atm.py
