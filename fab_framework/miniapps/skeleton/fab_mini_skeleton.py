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
        dirs = ['infrastructure/source/', 'components/driver/source/',
                'components/inventory/source/', 'components/science/source/',
                'components/lfric-xios/source/',
                'miniapps/skeleton/source/']

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_root / dir, dst_label='')

    def get_rose_meta(self):
        return (self.lfric_root / 'miniapps' / 'skeleton' / 'rose-meta' /
                'lfric-skeleton' / 'HEAD' / 'rose-meta.conf')

    def get_transformation_script(self):
        ''':returns: the transformation script to be used by PSyclone.
        :rtype: Path
        '''
        return ""


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_mini_skeleton = FabMiniSkeleton()
    fab_mini_skeleton.build()
