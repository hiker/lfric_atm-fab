#!/bin/bash

set -eu
set -o pipefail

echo 'current dir'
echo $PWD
export FAB_FRAMEWORK_REPO=$PWD

mkdir /scratch/hc46/hc46_gitlab/lfric_fab
export FAB_WORKSPACE=/scratch/hc46/hc46_gitlab/lfric_fab

# get the current lfric_core revision from the repo mirror
lfric_core_rev=$(svn info file:///g/data/ki32/mosrs/lfric/LFRic/trunk | grep Revision | sed 's/.* //g')
echo $lfric_core_rev > lfric_core_revision
cp lfric_core_revision $FAB_WORKSPACE/lfric_core_revision
export lfric_core_rev

# get the current lfric_apps revision from the repo mirror
lfric_apps_rev=$(svn info file:///g/data/ki32/mosrs/lfric_apps/main/trunk | grep Revision | sed 's/.* //g')
echo $lfric_apps_rev > lfric_apps_revision
cp lfric_apps_revision $FAB_WORKSPACE/lfric_apps_revision

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-fab-new-framework

# grab the lfric sources
echo "Start grabbing the lfric sources"
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort ./fab_framework/infrastructure/build/fab/grab_lfric.py
echo "Grabbed the lfric sources successfully"

# install the fab build scripts
echo "Start installing the fab build scripts"
cd fab_framework
echo 'current dir'
echo $PWD
export PATH_TO_CORE=$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/core
export PATH_TO_APPS=$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/apps
./install.sh $PATH_TO_CORE $PATH_TO_APPS
echo "Installed the fab build scripts"

cd ../
echo 'current dir'
echo $PWD
echo "Start building apps"

# Make sure the fab submodule exist:
if [[ ! -d $PWD/fab/source ]]; then
	echo "Error initialising the Fab submodule, $PWD/fab/source does not exist"
	exit 1
fi
export PYTHONPATH=$PWD/fab/source

# build lfric_atm
cd $PATH_TO_APPS/applications/lfric_atm/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE PYTHONPATH=$PYTHONPATH FC=   \
         CC=icc LD= $PATH_TO_CORE/build.sh \
         ./fab_lfric_atm.py --site nci --platform gadi --mpi       \
                      --suite intel-classic                        \
                      --fc mpif90-ifort -ld linker-mpif90-ifort


echo "Built lfric_atm"

cd $FAB_FRAMEWORK_REPO
echo "current dir"
echo $PWD
cp job.log $FAB_WORKSPACE/job_build.log
echo "Finished building"
