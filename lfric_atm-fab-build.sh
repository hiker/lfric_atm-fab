#!/bin/bash

echo 'current dir'
echo $PWD

# get the current lfric_core revision from the repo mirror
lfric_core_rev=$(svn info file:///g/data/ki32/mosrs/lfric/LFRic/trunk | grep Revision | sed 's/.* //g')
echo $lfric_core_rev > lfric_core_revision

# get the current lfric_apps revision from the repo mirror
lfric_apps_rev=$(svn info file:///g/data/ki32/mosrs/lfric_apps/main/trunk | grep Revision | sed 's/.* //g')
echo $lfric_apps_rev > lfric_apps_revision

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-lfric-fab

# grab the lfric sources
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/grab_lfric.py

# build lfric_atm
imagerun FAB_WORKSPACE=$PWD FC=ifort ./scripts/atm.py

mv lfric_source_${rev}/source/lfric/lfric_atm/example .
mv lfric_source_${rev}/source/lfric/lfric_atm/metadata .

cp atm_ifort_1stage/lfric_atm.exe .
