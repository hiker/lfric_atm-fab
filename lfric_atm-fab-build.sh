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
./install.sh $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps
echo "Installed the fab build scripts"

cd ../
echo 'current dir'
echo $PWD
echo "Start building apps"

export PYTHONPATH=/opt/spack/.local/lib/python3.12/site-packages/:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/fab

# build skeleton
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/miniapps/skeleton/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_mini_skeleton.py

echo "Built skeleton"

# build gungho_model
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/gungho_model/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_gungho_model.py

echo "Built gungho_model"

# build gravity_wave
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/gravity_wave/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_gravity_wave.py

echo "Built gravity_wave"

# build lfric_atm
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/lfric_atm/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_lfric_atm.py

echo "Built lfric_atm"

# build lfric_inputs
cd $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/lfricinputs/
echo "current dir"
echo $PWD
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_lfric2um.py
imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_um2lfric.py

echo "Built lfric_inputs"

cd $FAB_FRAMEWORK_REPO
echo "current dir"
echo $PWD
echo "Finished building"