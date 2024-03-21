#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

import sys
from fab.build_config import BuildConfig
from fab.steps.grab.fcm import fcm_export
from fab.steps.grab.folder import grab_folder


LFRIC_REVISION = 47450
#ROSE_PICKER_REVISION = 30163
ROSE_PICKER_REVISION = 47450


# these configs are interrogated by the build scripts
# todo: doesn't need two separate configs, they use the same project workspace
lfric_source_config = BuildConfig(project_label=f'lfric source {LFRIC_REVISION}')
gpl_utils_source_config = BuildConfig(project_label=f'lfric source {ROSE_PICKER_REVISION}')


if __name__ == '__main__':

    if len(sys.argv) > 1:
        print ("Yep")
        with lfric_source_config:
            grab_folder(lfric_source_config, src=sys.argv[1])
    else:
        with lfric_source_config:
            fcm_export(
                lfric_source_config, src='fcm:lfric.xm_tr', revision=LFRIC_REVISION, dst_label='lfric')

        with gpl_utils_source_config:
            fcm_export(
                gpl_utils_source_config, src='fcm:lfric_gpl_utils.xm-tr', revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')
