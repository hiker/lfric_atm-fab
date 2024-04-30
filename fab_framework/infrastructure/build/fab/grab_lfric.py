#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################
import os
import sys

from fab.build_config import BuildConfig
from fab.steps.grab.fcm import fcm_export
from fab.steps.grab.folder import grab_folder
from fab.newtools import ToolBox

fab_workspace = os.getenv('FAB_WORKSPACE')

lfric_core_rev_file = fab_workspace + '/lfric_core_revision'
lfric_apps_rev_file = fab_workspace + '/lfric_apps_revision'

file=open(lfric_core_rev_file,'r')
LFRIC_CORE_REVISION=file.readline().strip('\n')
file.close()
print('lfric core revision: ' + LFRIC_CORE_REVISION)

file=open(lfric_apps_rev_file,'r')
LFRIC_APPS_REVISION=file.readline().strip('\n')
file.close()
print('lfric apps revision: ' + LFRIC_APPS_REVISION)

ROSE_PICKER_REVISION=LFRIC_CORE_REVISION

print('lfric core revision: ' + LFRIC_CORE_REVISION)
print('rose-picker revision: ' + ROSE_PICKER_REVISION)

# these configs are interrogated by the build scripts
# todo: doesn't need two separate configs, they use the same project workspace
lfric_core_source_config = BuildConfig(project_label=f'lfric source {LFRIC_CORE_REVISION}',
                                       tool_box=ToolBox(),
                                      )
lfric_apps_source_config = BuildConfig(project_label=f'lfric source {LFRIC_CORE_REVISION}',
                                       tool_box=ToolBox(),
                                      )
gpl_utils_source_config = BuildConfig(project_label=f'lfric source {ROSE_PICKER_REVISION}',
                                      tool_box=ToolBox()
                                     )

if __name__ == '__main__':

    if len(sys.argv) > 1:
        with lfric_core_source_config:
            grab_folder(lfric_core_source_config, src=sys.argv[1])

    else:
        with lfric_core_source_config:
            fcm_export(
                lfric_core_source_config, src='fcm:lfric.xm_tr', revision=LFRIC_CORE_REVISION, dst_label='lfric_core')
            
        with lfric_apps_source_config:
            fcm_export(
                lfric_apps_source_config, src='fcm:lfric_apps.xm_tr', revision=LFRIC_APPS_REVISION, dst_label='lfric_apps')

        with gpl_utils_source_config:
            fcm_export(
                gpl_utils_source_config, src='file:///g/data/ki32/mosrs/lfric/GPL-utilities/tags/v2.0.0/', revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')
