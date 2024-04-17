#!/bin/bash

echo 'current dir'
echo $PWD

# get the current lfric_core revision from the repo mirror
lfric_core_rev=$(svn info file:///g/data/ki32/mosrs/lfric/LFRic/trunk | grep Revision | sed 's/.* //g')
echo $lfric_core_rev > lfric_core_revision
export lfric_core_rev

# get the current lfric_apps revision from the repo mirror
lfric_apps_rev=$(svn info file:///g/data/ki32/mosrs/lfric_apps/main/trunk | grep Revision | sed 's/.* //g')
echo $lfric_apps_rev > lfric_apps_revision

# load the container
module use /scratch/hc46/hc46_gitlab/ngm/modules/
module load lfric-v0/intel-openmpi-fab-new-framework

# grab the lfric sources
echo "Start grabbing the lfric sources"

export FAB_WORKSPACE=$PWD

imagerun FAB_WORKSPACE=$PWD FC=ifort ./fab_framework/infrastructure/build/fab/grab_lfric.py

echo "Grabbed the lfric sources successfully"

echo 'current dir'

ls

# install the fab build scripts
echo "Start installing the fab build scripts"

cd fab_framework

echo 'current dir'

echo $PWD

./install.sh $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps

echo "Installed the fab build scripts"

ls

cd ../

echo 'current dir'

echo $PWD

ls

echo "Start building apps"

# build skeleton
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/miniapps/skeleton/fab_mini_skeleton.py

echo "Built skeleton"

# build gungho_model
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/gungho_model/fab_gungho_model.py

echo "Built gungho_model"

# build gravity_wave
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/gravity_wave/fab_gravity_wave.py

echo "Built gravity_wave"

# build lfric_atm
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/lfric_atm/fab_lfric_atm.py

echo "Built lfric_atm"

# build lfric_inputs
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/lfricinputs/fab_lfric2um.py
imagerun FAB_WORKSPACE=$PWD FC=ifort PYTHONPATH=$PYTHONPATH:$FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_core/infrastructure/build/psyclone $FAB_WORKSPACE/lfric_source_${lfric_core_rev}/source/lfric_apps/applications/lfricinputs/um2lfric.py

echo "Built lfric_inputs"

echo "Finished building"
