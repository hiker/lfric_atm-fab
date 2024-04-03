In order to use the new FAB scripts on NCI, the following steps are required
(besides making sure that the required software dependencies are available
for compilation and you already have a clean LFRic checkout)

1. Load module python3/3.12.1

2. pip3 install --user libclang

3. Make sure to have a recent version of PSyclone installed (ideally 2.5 or later,
   though older versions might work)

4. export PSYCLONE_CONFIG=ROOT_OF_YOUR_LFRIC/etc/psyclone.cfg
	(to be properly fixed later :) )
   export PYTHONPATH=$PYTHONPATH:ROOT_OF_YOUR_LFRIC/infrastructure/build/psyclone
    (add the psyclone_tools module)

5. Export FAB_WORKSPACE if required

6. Make sure our git version fab is installed. You must have a recent version
   of python installed (python3/3.12.1 works), or else you will get an error
   message when trying to install fab.

	   git clone git@github.com:hiker/fab.git
	   cd fab
	   pip install --user -e .      # Don't forget the .
	   # Switch to a temporary branch that contains some not-yet-merged patches:
	   git checkout joerg_all_patches
	   cd fab_framework
	   # Copy the build scripts into your lfric build:
	   ./install.sh $ROOT_OF_YOUR_LFRIC
	   
6. Grab a copy of rose-picker (to be properly fixed later):
   	cd ROOT_OF_YOUR_LFRIC/infrastructure/build/fab
   	./grab_lfric_utils.py

7. Modify compilation flags and compiler as required ... sorry, very
   messy hack. Fix the constructor. It is set for ifort ... kind of,
   but still has incorrect (e.g. gfortran) flags ... work in progress
       cd ROOT_OF_YOUR_LFRIC/infrastructure/build/fab
       vi fab_base.py

8. Now ... you should be ready:
       cd ROOT_OF_YOUR_LFRIC/lfric_inputs
       ./fab_um2lfric.py
		 ./fab_lfric2um.py
	The files will be built in the same fab workspace lfric_inputs-intel
