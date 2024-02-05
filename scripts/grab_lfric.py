#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################
import os

from fab.build_config import BuildConfig
from fab.steps.grab.fcm import fcm_export

TOKEN = os.getenv('CI_RUNNER_SHORT_TOKEN')
rev_file = '/scratch/hc46/hc46_gitlab/builds/'+TOKEN+'/0/bom/ngm/lfric/lfric_atm-fab/lfric_revision'

file=open(rev_file,'r')
LFRIC_REVISION=file.readline().strip('\n')
file.close()
LFRIC_REVISION='46556'
print('lfric revision: ' + LFRIC_REVISION)

ROSE_PICKER_REVISION=LFRIC_REVISION

print('lfric revision: ' + LFRIC_REVISION)
print('rose-picker revision: ' + ROSE_PICKER_REVISION)

# these configs are interrogated by the build scripts
# todo: doesn't need two separate configs, they use the same project workspace
lfric_source_config = BuildConfig(project_label=f'lfric source {LFRIC_REVISION}')
gpl_utils_source_config = BuildConfig(project_label=f'lfric source {ROSE_PICKER_REVISION}')

if __name__ == '__main__':
    with lfric_source_config:
        fcm_export(
            lfric_source_config, src='fcm:lfric.xm_tr', revision=LFRIC_REVISION, dst_label='lfric')

    with gpl_utils_source_config:
        fcm_export(gpl_utils_source_config, src='file:///g/data/ki32/mosrs/lfric/GPL-utilities/tags/v2.0.0/', revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')
        #fcm_export(gpl_utils_source_config, src='fcm:lfric_gpl_utils.xm-tr', revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')
