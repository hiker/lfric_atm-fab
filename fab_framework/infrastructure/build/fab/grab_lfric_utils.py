#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A simple grab script that downloads rose picker from the
subversion repository.
'''

from fab.build_config import BuildConfig
from fab.steps.grab.fcm import fcm_export
from fab.newtools import ToolBox

LFRIC_REVISION = 47450
ROSE_PICKER_REVISION = 47450


# this config is used by the build scripts
gpl_utils_source_config = BuildConfig(
    project_label=f'lfric source {ROSE_PICKER_REVISION}',
    tool_box=ToolBox())


if __name__ == '__main__':

    with gpl_utils_source_config:
        fcm_export(
            gpl_utils_source_config, src='fcm:lfric_gpl_utils.xm-tr',
            revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')
