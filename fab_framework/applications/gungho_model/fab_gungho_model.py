#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for gungho_model. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../../../core/infrastructure/build/fab")

from fab.steps.grab.folder import grab_folder

from fab_base import FabBase


class FabGungho(FabBase):

    def __init__(self, name="gungho_model", root_symbol=None):
        super().__init__(name, root_symbol=root_symbol)

        self.set_preprocessor_flags(
            ['-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=64',
             '-DR_TRAN_PRECISION=64', '-DUSE_XIOS'])

    def grab_files(self):
        FabBase.grab_files(self)
        dirs = ['applications/gungho_model/source/',
                'science/gungho/source',
                ]
        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_apps_root / dir,
                        dst_label='')

        # Copy the optimisation scripts into a separate directory
        dir = 'applications/gungho_model/optimisation'
        grab_folder(self.config, src=self.lfric_apps_root / dir,
                    dst_label='optimisation')

    def get_rose_meta(self):
        return (self.lfric_apps_root / 'applications' / 'gungho_model'
                / 'rose-meta' / 'lfric-gungho_model' / 'HEAD'
                / 'rose-meta.conf')


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_gungo = FabGungho()
    fab_gungo.build()
