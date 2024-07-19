#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for mesh_tools. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys

from fab.steps.grab.folder import grab_folder
from fab.steps.analyse import analyse

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../infrastructure/build/fab")

from fab_base import FabBase


class FabMeshTool(FabBase):

    def __init__(self, name="mesh_tools", root_symbol=None):
        super().__init__(name, root_symbol=root_symbol)

    def grab_files(self):
        FabBase.grab_files(self)
        dirs = ['mesh_tools/source/']

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_core_root / dir,
                        dst_label='')

    def get_rose_meta(self):
        return (self.lfric_core_root / 'mesh_tools' / 'rose-meta' /
                'lfric-mesh_tools' / 'HEAD' / 'rose-meta.conf')


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_mesh_tool = FabMeshTool(root_symbol= \
                                ['cubedsphere_mesh_generator', \
                                 'planar_mesh_generator', \
                                    'summarise_ugrid'])
    fab_mesh_tool.build()