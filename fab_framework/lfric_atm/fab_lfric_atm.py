#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for lfric_atm. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys

from fab.steps.grab.fcm import fcm_export
from fab.steps.grab.folder import grab_folder
from fab.build_config import AddFlags
from fab.steps.find_source_files import Exclude, Include

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../infrastructure/build/fab")

from fab_base import FabBase
from grab_lfric import gpl_utils_source_config

from fcm_extract import FcmExtract

class FabMiniGungho(FabBase):

    def __init__(self, name="lfric_atm", root_symbol=None):
        super().__init__(name, gpl_utils_source_config,
                         root_symbol=root_symbol)

        self.set_preprocessor_flags(
            ['-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=32',
             '-DR_TRAN_PRECISION=64', '-DUSE_XIOS', '-DUM_PHYSICS',
             '-DCOUPLED', '-DUSE_MPI=YES'])

    def grab_files(self):
        dirs = ['infrastructure/source/', 'components/driver/source/',
                'components/inventory/source/', 'components/science/source/',
                'components/lfric-xios/source/',
                'components/coupler-oasis/source/',
                'gungho/source/', 
                'um_physics/source/', 'socrates/source/', 'jules/source/',
                'lfric_atm/source']
        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_root / dir, dst_label='')


        um = "https://code.metoffice.gov.uk/svn/um/main/trunk/src"
        #fcm_export(self.config, src=um, dst_label='science/um', revision='123015')
        jules="https://code.metoffice.gov.uk/svn/jules/main/trunk/src"
        #fcm_export(self.config, src=jules, dst_label='science/jules', revision='27996')
        socrates = "https://code.metoffice.gov.uk/svn/socrates/main/trunk/src"
        #fcm_export(self.config, src=socrates, dst_label='science/socrates', revision='1483')
        shumlib = "https://code.metoffice.gov.uk/svn/utils/shumlib/trunk"
        #fcm_export(self.config, src=shumlib, dst_label='science/shumlib', revision="7198")
        casim = "https://code.metoffice.gov.uk/svn/monc/casim/trunk/src"
        #fcm_export(self.config, src=casim, dst_label='science/casim', revision='10614')
        ukca = "https://code.metoffice.gov.uk/svn/ukca/main/trunk/src"
        #fcm_export(self.config, src=ukca, dst_label='science/ukca', revision="3196")

        # Copy the optimisation scripts into a separate directory
        dir = 'lfric_atm/optimisation'
        grab_folder(self.config, src=self.lfric_root / dir,
                    dst_label='optimisation')

    def find_source_files(self):
        """Based on lfric_atm/fcm-make/extract.cfg"""

        extract = FcmExtract(self.lfric_root / "lfric_atm" / "fcm-make" /
                          "extract.cfg")
        
        science_root = self.config.source_root / 'science'
        path_filters = []
        for section, source_file_info in extract.items():
            for (list_type, list_of_paths) in source_file_info:
                if list_type == "exclude":
                    path_filters.append(Exclude(science_root / section))
                else:
                    # Remove the 'src' which is the first part of the name
                    new_paths = [i.relative_to(i.parents[-2]) for i in list_of_paths]
                    for path in new_paths:
                        path_filters.append(Include(science_root / section / path))
        super().find_source_files(path_filters=path_filters)


    def get_rose_meta(self):
        return None
        return (self.lfric_root / 'lfric_atm' / 'rose-meta' /
                'lfric-lfric_atm' / 'HEAD' / 'rose-meta.conf')

    def preprocess_c(self):
        path_flags=[AddFlags(match="$source/science/um/*", flags=['-I$relative/include',
                                                                  '-I/$source/science/um/include/other/',
                                                                  '-I$source/science/shumlib/common/src',
                                                                  '-I$source/science/shumlib/shum_thread_utils/src',]),
                    AddFlags(match="$source/science/jules/*", flags=['-DUM_JULES', '-I$output']),
                    AddFlags(match="$source/science/shumlib/*", flags=['-DSHUMLIB_LIBNAME=libshum',
                                                                       '-I$output',
                                                                       '-I$source/science/shumlib/common/src',
                                                                       '-I$source/science/shumlib/shum_thread_utils/src',
                                                                       '-I$relative'],),
                    AddFlags(match="$source/science/8", flags=['-DLFRIC']) ]
        super().preprocess_c(path_flags=path_flags)


    def preprocess_fortran(self):
        path_flags=[AddFlags(match="$source/science/um/*", flags=['-I$relative/include',
                                                                  '-I$source/shumlib/shum_thread_utils/src/']),
                    AddFlags(match="$source/science/jules/*", flags=['-DUM_JULES', '-I$output']),
                    AddFlags(match="$source/science/shumlib/*", flags=['-DSHUMLIB_LIBNAME=libshum',
                                                                       '-I$output',
                                                                       '-I$source/shumlib/common/src',
                                                                       '-I$relative'],),
                    AddFlags(match="$source/science/*", flags=['-DLFRIC']) ]
        super().preprocess_fortran(path_flags=path_flags)

    def get_transformation_script(self):
        ''':returns: the transformation script to be used by PSyclone.
        :rtype: Path
        '''
        return self.config.source_root / "optimisation/nci-gadi/global.py"


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_mini_gungo = FabMiniGungho()
    fab_mini_gungo.build()
