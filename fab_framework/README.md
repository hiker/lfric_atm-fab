In order to use the new FAB scripts on NCI, you can follow these steps:

1. Load the container for all software dependencies:
	`module use /scratch/hc46/hc46_gitlab/ngm/modules`
	`module load lfric-v0/intel-openmpi-fab-new-framework`
	
2. Find a suitable space for FAB:
    `export FAB_WORKSPACE=$PWD`

3. Grab the lfric sources
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort ./fab_framework/infrastructure/build/fab/grab_lfric.py`

4. Install the FAB build scripts
	`cd ./fab_framework`
	`./install.sh PATH_TO_LFRIC_CORE PATH_TO_LFRIC_APPS`

5. Export PYTHONPATH for FAB
	`export PYTHONPATH=/opt/spack/.local/lib/python3.12/site-packages/:PATH_TO_LFRIC_CORE/infrastructure/build/psyclone`

6. Go into the app directory and start building
	(1)Skeleton:
	`cd PATH_TO_LFRIC_CORE/miniapps/skeleton`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_mini_skeleton.py`
	(2)Gungho_model:
	`cd PATH_TO_LFRIC_APPS/applications/gungho_model`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_gungho_model.py`
	(3)Gravity wave:
	`cd PATH_TO_LFRIC_APPS/applications/gravity_wave`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_gravity_wave.py`
	(4)LFRic_atm:
	`cd PATH_TO_LFRIC_APPS/applications/lfric_atm`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_lfric_atm.py`
	(5)LFRicinputs:
	`cd PATH_TO_LFRIC_APPS/applications/lfricinputs`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_lfric2um.py`
	`imagerun FAB_WORKSPACE=$FAB_WORKSPACE FC=ifort PYTHONPATH=$PYTHONPATH ./fab_um2lfric.py`
