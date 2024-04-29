#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for miniapps/skeleton. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys
from fnmatch import fnmatch
from string import Template

from fab.steps.grab.folder import grab_folder

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../../infrastructure/build/fab")

from fab_base import FabBase
from grab_lfric import gpl_utils_source_config


class FabMiniSkeleton(FabBase):

    def __init__(self, name="skeleton", root_symbol=None):
        super().__init__(name, gpl_utils_source_config,
                         root_symbol=root_symbol)

        self.set_preprocessor_flags(
            ['-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=64',
             '-DR_TRAN_PRECISION=64', '-DUSE_XIOS'])

    def grab_files(self):
        FabBase.grab_files(self)
        dirs = ['miniapps/skeleton/source/']

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_core_root / dir, dst_label='')

        # Copy the optimisation scripts into a separate directory
        dir = 'miniapps/skeleton/optimisation'
        grab_folder(self.config, src=self.lfric_core_root / dir,
                    dst_label='optimisation')

    def get_rose_meta(self):
        return (self.lfric_core_root / 'miniapps' / 'skeleton' / 'rose-meta' /
                'lfric-skeleton' / 'HEAD' / 'rose-meta.conf')

    def get_transformation_script(self, fpath):
        ''':returns: the transformation script to be used by PSyclone.
        :rtype: Path
        '''
        params = {'relative': fpath.parent, 'source': self.config.source_root, 'output': self.config.build_output}
        global_transformation_script = None
        local_transformation_script = None
        global_transformation_script = '$source/optimisation/nci-gadi/global.py'
        local_transformation_script = {'$source/algorithm/solver/*':"$source/optimisation/nci-gadi/global1.py",
                                       '$source/algorithm/galerkin*':'$source/optimisation/nci-gadi/global2.py',
                                       '$source/algorithm/sci*':'$source/optimisation/nci-gadi/global3.py',
                                       }
        if global_transformation_script: 
            if local_transformation_script: 
                #global defined, local defined
                for key_match in local_transformation_script:
                    if fnmatch(str(fpath), Template(key_match).substitute(params)):
                        # use templating to render any relative paths
                        return Template(local_transformation_script[key_match]).substitute(params)        
                return Template(global_transformation_script).substitute(params)
            else:
                #global defined, local not defined
                return Template(global_transformation_script).substitute(params)
        elif local_transformation_script:   
                #global not defined, local defined 
            for key_match in local_transformation_script:
                if fnmatch(str(fpath), Template(key_match).substitute(params)):
                    # use templating to render any relative paths
                    return Template(local_transformation_script[key_match]).substitute(params)          
            return ""
        else:                               
                #global not defined, local not defined
            return ""


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_mini_skeleton = FabMiniSkeleton()
    fab_mini_skeleton.build()
