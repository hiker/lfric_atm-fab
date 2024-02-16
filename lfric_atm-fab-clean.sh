#!/bin/bash

cd /scratch/hc46/hc46_gitlab/builds/$CI_RUNNER_SHORT_TOKEN
echo $PWD
rm -rf 0/bom/ngm/lfric/lfric_atm-fab
rm -rf 1/bom/ngm/lfric/lfric_atm-fab
rm -rf 2/bom/ngm/lfric/lfric_atm-fab
rm -rf 3/bom/ngm/lfric/lfric_atm-fab
rm -rf /scratch/hc46/hc46_gitlab/builds/0/bom/ngm/lfric/lfric_atm-fab
rm -rf /scratch/hc46/hc46_gitlab/cylc-run/gungho_nightly
rm -rf /scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_developer
rm -rf /scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly
rm -rf /scratch/hc46/hc46_gitlab/cylc-run/lfric_apps-nightly
