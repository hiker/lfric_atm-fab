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

#LFRIC_REVISION = int(sys.argv[1])
#ROSE_PICKER_REVISION = int(sys.argv[1])

TOKEN = os.getenv('CI_RUNNER_SHORT_TOKEN')
rev_file = '/scratch/hc46/hc46_gitlab/builds/'+TOKEN+'/0/bom/ngm/lfric/lfric_atm-fab/lfric_revision'

file=open(rev_file,'r')
LFRIC_REVISION=file.readline().strip('\n')
file.close()
print('lfric revision: ' + LFRIC_REVISION)

# these configs are interrogated by the build scripts
# todo: doesn't need two separate configs, they use the same project workspace
lfric_source_config = BuildConfig(project_label=f'lfric source {LFRIC_REVISION}')
#gpl_utils_source_config = BuildConfig(project_label=f'lfric source {ROSE_PICKER_REVISION}')
gpl_utils_source_config = BuildConfig(project_label=f'lfric source {LFRIC_REVISION}')

if __name__ == '__main__':
    with lfric_source_config:
        fcm_export(
            lfric_source_config, src='fcm:lfric.xm_tr', revision=LFRIC_REVISION, dst_label='lfric')

    with gpl_utils_source_config:
        fcm_export(
            gpl_utils_source_config, src='fcm:lfric_gpl_utils.xm-tr', revision=LFRIC_REVISION, dst_label='gpl_utils')
            #gpl_utils_source_config, src='fcm:lfric_gpl_utils.xm-tr', revision=ROSE_PICKER_REVISION, dst_label='gpl_utils')