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
from fab.tools import Category

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../../../core/infrastructure/build/fab")

from fab_base import FabBase
from get_revision import GetRevision

from fcm_extract import FcmExtract

class FabLFRicAtm(FabBase):

    def __init__(self, name="lfric_atm", root_symbol=None):
        super().__init__(name, root_symbol=root_symbol)

        self.set_preprocessor_flags(
            ['-DUM_PHYSICS',
             '-DCOUPLED', '-DUSE_MPI=YES'])

    def grab_files(self):
        FabBase.grab_files(self)
        dirs = ['science/coupled_interface/source/',
                'science/gungho/source', 
                'science/um_physics_interface/source/', 
                'science/socrates_interface/source/', 
                'science/jules_interface/source/',
                'applications/lfric_atm/source',
                'science/constants/source',
                ]
        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_apps_root / dir, dst_label='')

        gr = GetRevision("../../dependencies.sh")
        xm = "xm"
        for lib, revision in gr.items():
            # Shumlib has no src directory
            if lib == "shumlib":
                src = ""
            else:
                src = "/src"
            print(f'fcm:{lib}.{xm}_tr{src}', f'science/{lib}', revision)
            fcm_export(self.config, src=f'fcm:{lib}.{xm}_tr/{src}',
                       dst_label=f'science/{lib}',revision=revision)

        # Copy the optimisation scripts into a separate directory
        dir = 'applications/lfric_atm/optimisation'
        grab_folder(self.config, src=self.lfric_apps_root / dir,
                    dst_label='optimisation')

    def find_source_files(self):
        """Based on $LFRIC_APPS_ROOT/build/extract/extract.cfg"""

        extract = FcmExtract(self.lfric_apps_root / "build" / "extract" /
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
        return (self.lfric_apps_root / 'applications/lfric_atm' / 'rose-meta' /
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

    def compile_fortran(self):
        fc = self.config.tool_box[Category.FORTRAN_COMPILER]
        # TODO: needs a better solution, we are still hardcoding compilers here
        if fc.suite == "intel-classic":
            no_omp = '-qno-openmp'
        else:
            no_omp = '-fno-openmp'
        path_flags=[AddFlags('$output/science/um/atmosphere/large_scale_precipitation/*',
                             [no_omp]),
                    AddFlags(match="$output/science/*", flags=['-r8']), ]
        # TODO: A remove flag functionality based on profile option and precision is needed
        if self._args.profile == 'full-debug':
            self._compiler_flags.remove('-check all,noshape') if '-check all,noshape' in self._compiler_flags \
                else self._compiler_flags.remove('-check all')
        super().compile_fortran(path_flags=path_flags)


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_lfric_atm = FabLFRicAtm()
    fab_lfric_atm.build()