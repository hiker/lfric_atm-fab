#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for applications/skeleton. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys

from fab.steps.grab.folder import grab_folder

from fab_base import FabBase


class FabSkeleton(FabBase):

    def __init__(self, name="skeleton", root_symbol=None):
        super().__init__(name, root_symbol=root_symbol)

    def grab_files(self):
        FabBase.grab_files(self)
        dirs = ['applications/skeleton/source/']

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_core_root / dir,
                        dst_label='')

        # Copy the optimisation scripts into a separate directory
        dir = 'applications/skeleton/optimisation/'
        grab_folder(self.config, src=self.lfric_core_root / dir,
                    dst_label='optimisation')

    def get_rose_meta(self):
        return (self.lfric_core_root / 'applications' / 'skeleton' / 'rose-meta' /
                'lfric-skeleton' / 'HEAD' / 'rose-meta.conf')


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_skeleton = FabSkeleton()
    fab_skeleton.build()
