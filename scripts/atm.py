#!/usr/bin/env python3
import os
import re
import warnings

import logging

from fab.build_config import BuildConfig, AddFlags
from fab.steps.analyse import analyse
from fab.steps.archive_objects import archive_objects
from fab.steps.c_pragma_injector import c_pragma_injector
from fab.steps.compile_c import compile_c
from fab.steps.compile_fortran import compile_fortran
from fab.steps.grab.fcm import fcm_export
from fab.steps.grab.folder import grab_folder
from fab.steps.link import link_exe
from fab.steps.preprocess import preprocess_fortran, preprocess_c
from fab.steps.psyclone import psyclone, preprocess_x90
from fab.steps.find_source_files import find_source_files, Exclude, Include

from grab_lfric import lfric_source_config, gpl_utils_source_config
from lfric_common import configurator, fparser_workaround_stop_concatenation

logger = logging.getLogger('fab')

# todo: optimisation path stuff

def case_insensitive_replace(in_str: str, find: str, replace_with: str):
    compiled_re = re.compile(find, re.IGNORECASE)
    return compiled_re.sub(replace_with, in_str)

def replace_in_file(file_path, find, replace):
    orig = open(os.path.expanduser(file_path), "rt").read()
    open(os.path.expanduser(file_path), "wt").write( \
         case_insensitive_replace(in_str=orig, find=find,\
                                  replace_with=replace))

def get_psyclone_transformation():
    if os.getenv("PSYCLONE_TRANSFORMATION"):
        return os.getenv("PSYCLONE_TRANSFORMATION")
    else:
        return 'meto-spice'

def file_filtering(config):
    """Based on lfric_atm/fcm-make/extract.cfg"""

    science_root = config.source_root / 'science'

    return [
        Exclude('unit-test', '/test/'),

        Exclude(science_root / 'um'),
		Include(science_root / 'um/atmosphere/AC_assimilation/iau_mod.F90'),
		Include(science_root / 'um/atmosphere/PWS_diagnostics/pws_diags_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/aero_params_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/arcl_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/c_sulchm_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/calc_pm_diags_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/calc_surf_area_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/dms_flux_4A.F90'),
		Include(science_root / 'um/atmosphere/aerosols/dust_parameters_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/grow_particles_mod.F90'),
		Include(science_root / 'um/atmosphere/aerosols/run_aerosol_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/calc_wp.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/calc_wp_below_t.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/fog_fr.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/include/qsat_mod_qsat.h'),
		Include(science_root / 'um/atmosphere/atmosphere_service/include/qsat_mod_qsat_mix.h'),
		Include(science_root / 'um/atmosphere/atmosphere_service/murk_inputs_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/number_droplet_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/qsat_data_real32_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/qsat_data_real64_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/qsat_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/vis_precip.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/visbty.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/visbty_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/atmosphere_service/vistoqt.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bdy_expl2.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bdy_impl3.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bdy_impl4.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bl_diags_mod.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bl_lsp.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/bl_option_mod.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/btq_int.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/buoy_tq.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/include/buoy_tq.h'),
		Include(science_root / 'um/atmosphere/boundary_layer/dust_calc_emiss_frac.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/dust_srce.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/ex_coef.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/ex_flux_tq.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/ex_flux_uv.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/excf_nl_9c.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/excfnl_cci.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/excfnl_compin.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/fm_drag.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/imp_mix.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/kmkh.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/kmkhz_9c.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/kmkhz_9c_wtrac.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/mym_option_mod.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/sblequil.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/tr_mix.F90'),
		Include(science_root / 'um/atmosphere/boundary_layer/wtrac_bl.F90'),
		Include(science_root / 'um/atmosphere/carbon/carbon_options_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/calc_3d_cca-cal3dcca.F90'),
		Include(science_root / 'um/atmosphere/convection/calc_w_eqn.F90'),
		Include(science_root / 'um/atmosphere/convection/chg_phse-chgphs3c.F90'),
		Include(science_root / 'um/atmosphere/convection/cloud_w_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/cloud_w_wtrac.F90'),
		Include(science_root / 'um/atmosphere/convection/cmt_heating_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/cmt_mass-cmtmass4a.F90'),
		Include(science_root / 'um/atmosphere/convection/column_rh_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/comorph/control/comorph_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/con_rad_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/congest_conv_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/conv_diag-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/conv_diag_comp-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/conv_surf_flux.F90'),
		Include(science_root / 'um/atmosphere/convection/conv_type_defs.F90'),
		Include(science_root / 'um/atmosphere/convection/convec2_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/cor_engy_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/correct_small_q_conv.F90'),
		Include(science_root / 'um/atmosphere/convection/crs_frzl-crsfrz3c.F90'),
		Include(science_root / 'um/atmosphere/convection/cumulus_test_5a.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_dependent_switch_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_derived_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_diag_param_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_hist_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_param_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_parcel_neutral_dil.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_parcel_neutral_inv.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_run_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_set_dependent_switches.F90'),
		Include(science_root / 'um/atmosphere/convection/cv_stash_flg_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/dd_all_call-ddacall6a.F90'),
		Include(science_root / 'um/atmosphere/convection/dd_call-ddcall6a.F90'),
		Include(science_root / 'um/atmosphere/convection/dd_env-ddenv6a.F90'),
		Include(science_root / 'um/atmosphere/convection/dd_init-ddinit6a.F90'),
		Include(science_root / 'um/atmosphere/convection/ddraught-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_cmt_incr-dpcmtinc4a.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_conv_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_grad_stress-dpgrstrs4a.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_ngrad_stress-dpngstrs4a.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_turb_cmt.F90'),
		Include(science_root / 'um/atmosphere/convection/deep_turb_grad_stress.F90'),
		Include(science_root / 'um/atmosphere/convection/det_rate_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/detrain_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/devap-devap3a.F90'),
		Include(science_root / 'um/atmosphere/convection/downd-downd6a.F90'),
		Include(science_root / 'um/atmosphere/convection/eman_cex.F90'),
		Include(science_root / 'um/atmosphere/convection/eman_dd.F90'),
		Include(science_root / 'um/atmosphere/convection/eman_dd_rev.F90'),
		Include(science_root / 'um/atmosphere/convection/environ_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/environ_wtrac.F90'),
		Include(science_root / 'um/atmosphere/convection/evap_bcb_nodd-evapud6a.F90'),
		Include(science_root / 'um/atmosphere/convection/evap_bcb_nodd_all-evpuda6a.F90'),
		Include(science_root / 'um/atmosphere/convection/evp-evp3a.F90'),
		Include(science_root / 'um/atmosphere/convection/flag_wet-flagw3c.F90'),
		Include(science_root / 'um/atmosphere/convection/flx_init-flxini6a.F90'),
		Include(science_root / 'um/atmosphere/convection/glue_conv-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/init_conv6a_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/layer_cn_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/layer_dd-layerd6a.F90'),
		Include(science_root / 'um/atmosphere/convection/lift_cond_lev_5a.F90'),
		Include(science_root / 'um/atmosphere/convection/lift_par_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/lift_par_phase_chg_wtrac.F90'),
		Include(science_root / 'um/atmosphere/convection/lift_undil_par_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/llcs.F90'),
		Include(science_root / 'um/atmosphere/convection/mean_w_layer.F90'),
		Include(science_root / 'um/atmosphere/convection/mid_conv_dif_cmt.F90'),
		Include(science_root / 'um/atmosphere/convection/mid_conv_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/mix_ipert_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/parcel_ascent_5a.F90'),
		Include(science_root / 'um/atmosphere/convection/parcel_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/parcel_wtrac.F90'),
		Include(science_root / 'um/atmosphere/convection/pevp_bcb-5a.F90'),
		Include(science_root / 'um/atmosphere/convection/satcal-5a.F90'),
		Include(science_root / 'um/atmosphere/convection/shallow_base_stress-shbsstrs4a.F90'),
		Include(science_root / 'um/atmosphere/convection/shallow_cmt_incr-shcmtinc4a.F90'),
		Include(science_root / 'um/atmosphere/convection/shallow_conv_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/shallow_grad_stress-sgrdstrs4a.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_base_stress.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_calc_scales.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cb_stress.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_class_cloud.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_class_interface.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_class_scales.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_class_similarity.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_classes.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cloudbase.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cmt_incr-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cmt_incr.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cmt_params_dp.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_cmt_params_sh.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_common_warm.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_constants.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_grad_flux.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_grad_h.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_grad_stress.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_inversion.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_parameters_warm.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_pc2.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_precip.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_qlup.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_similarity.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_turb_fluxes.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_warm_mod.F90'),
		Include(science_root / 'um/atmosphere/convection/tcs_wql.F90'),
		Include(science_root / 'um/atmosphere/convection/term_con_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/termdd-termdd2a.F90'),
		Include(science_root / 'um/atmosphere/convection/thetar_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/thp_det_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/tridiag-tridia4a.F90'),
		Include(science_root / 'um/atmosphere/convection/tridiag_all.F90'),
		Include(science_root / 'um/atmosphere/convection/water_loading_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_conv.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_conv_store.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_gather_conv.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_precip_chg_phse.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_precip_evap.F90'),
		Include(science_root / 'um/atmosphere/convection/wtrac_scatter_conv.F90'),
		Include(science_root / 'um/atmosphere/diffusion_and_filtering/leonard_incs_mod.F90'),
		Include(science_root / 'um/atmosphere/diffusion_and_filtering/turb_diff_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/dynamics_input_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/dynamics_testing_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/gcr_input_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/helmholtz_const_matrix_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/horiz_grid_4A_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/imbnd_data_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/lbc_input_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/precon_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics/var_input_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics_advection/eg_alpha_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics_advection/eg_alpha_ramp_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics_advection/level_heights_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics_advection/problem_mod.F90'),
		Include(science_root / 'um/atmosphere/dynamics_advection/trignometric_mod.F90'),
		Include(science_root / 'um/atmosphere/electric/define_storm.F90'),
		Include(science_root / 'um/atmosphere/electric/electric_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/electric/electric_inputs_mod.F90'),
		Include(science_root / 'um/atmosphere/electric/flash_rate_mod.F90'),
		Include(science_root / 'um/atmosphere/electric/fr_gwp.F90'),
		Include(science_root / 'um/atmosphere/electric/fr_mccaul.F90'),
		Include(science_root / 'um/atmosphere/free_tracers/free_tracers_inputs_mod.F90'),
		Include(science_root / 'um/atmosphere/free_tracers/water_tracers_mod.F90'),
		Include(science_root / 'um/atmosphere/free_tracers/wtrac_all_phase_chg.F90'),
		Include(science_root / 'um/atmosphere/free_tracers/wtrac_calc_ratio.F90'),
		Include(science_root / 'um/atmosphere/free_tracers/wtrac_move_phase.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/c_gwave_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/g_wave_input_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_block.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_setup.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_core_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_params_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_prec_mod.F90'),
		Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_wave.F90'),
		Include(science_root / 'um/atmosphere/idealised/idealise_run_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/local_heat_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/planet_suite_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/profiles_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/surface_flux_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/tforce_mod.F90'),
		Include(science_root / 'um/atmosphere/idealised/trelax_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/bm_calc_tau.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/bm_cld.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/bm_ctl.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/bm_ez_diagnosis.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/c_cldsgs_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/cloud_inputs_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/ls_acf_brooks.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/ls_arcld.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/ls_cld.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/ls_cld_c.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_arcld.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_bl_forced_cu.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_bl_inhom_ice.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_bm_initiate.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_checks.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_checks2.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_checks_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_delta_hom_turb.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_environ_mod-6a.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_hom_arcld.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_hom_conv.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_homog_plus_turb.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_initiate.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_initiation_ctl.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/pc2_total_cf.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/wtrac_pc2.F90'),
		Include(science_root / 'um/atmosphere/large_scale_cloud/wtrac_pc2_phase_chg.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/CASIM/casim_prognostics.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/CASIM/casim_set_dependent_switches_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/CASIM/casim_switches.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/CASIM/mphys_die.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/beta_precip-btprec3c.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/gammaf-lspcon3c.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/include/lsp_moments.h'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/include/lsp_subgrid_lsp_qclear.h'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/ls_ppn.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/ls_ppnc.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_accretion.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_autoc.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_autoc_consts_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_capture.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_collection.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_combine_precfrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_deposition.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_deposition_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_dif_mod3c.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_evap.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_evap_snow.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_fall.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_fall_precfrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_froude_moist.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_gen_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_graup_autoc.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_het_freezing_rain.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_ice-lspice3d.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_init.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_init_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_melting.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_moments.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_nucleation.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_nucleation_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_orogwater.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_prognostic_tnuc.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_riming.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_scav.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_sedim_eulexp.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_sedim_eulexp_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_settle.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_settle_wtrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_snow_autoc.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_subgrid.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_taper_ndrop.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_tidy.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsp_update_precfrac.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lspcon-lspcon3c.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/lsprec_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_air_density_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_bypass_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_constants_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_diags_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_ice_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_inputs_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_psd_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_radar_mod.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_reflec.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/mphys_turb_gen_mixed_phase.F90'),
		Include(science_root / 'um/atmosphere/large_scale_precipitation/wtrac_mphys.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/def_easyaerosol.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/easyaerosol_option_mod.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/fsd_parameters_mod.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/max_calls.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/rad_input_mod.F90'),
		Include(science_root / 'um/atmosphere/radiation_control/solinc_data.F90'),
		Include(science_root / 'um/atmosphere/stochastic_physics/stochastic_physics_run_mod.F90'),
		Include(science_root / 'um/atmosphere/tracer_advection/trsrce-trsrce2a.F90'),
		Include(science_root / 'um/control/coupling/hybrid_control_mod.F90'),
		Include(science_root / 'um/control/dummy_libs/drhook/parkind1.F90'),
		Include(science_root / 'um/control/dummy_libs/drhook/yomhook.F90'),
		Include(science_root / 'um/control/glomap_clim_interface/glomap_clim_option_mod.F90'),
		Include(science_root / 'um/control/grids/nlsizes_namelist_mod.F90'),
		Include(science_root / 'um/control/grids/p_to_t.F90'),
		Include(science_root / 'um/control/grids/u_to_p.F90'),
		Include(science_root / 'um/control/grids/v_to_p.F90'),
		Include(science_root / 'um/control/misc/atmos_max_sizes.F90'),
		Include(science_root / 'um/control/misc/chk_opts_mod.F90'),
		Include(science_root / 'um/control/misc/compute_chunk_size_mod.F90'),
		Include(science_root / 'um/control/misc/control_max_sizes.F90'),
		Include(science_root / 'um/control/misc/field_types.F90'),
		Include(science_root / 'um/control/misc/science_fixes_mod.F90'),
		Include(science_root / 'um/control/misc/segments_mod.F90'),
		Include(science_root / 'um/control/misc/um_types.F90'),
		Include(science_root / 'um/control/misc/umerf_mod.F90'),
		Include(science_root / 'um/control/misc/vectlib_mod.F90'),
		Include(science_root / 'um/control/mpp/decomp_params.F90'),
		Include(science_root / 'um/control/mpp/um_parcore.F90'),
		Include(science_root / 'um/control/mpp/um_parparams.F90'),
		Include(science_root / 'um/control/mpp/um_parvars.F90'),
		Include(science_root / 'um/control/stash/copydiag_3d_mod.F90'),
		Include(science_root / 'um/control/stash/copydiag_mod.F90'),
		Include(science_root / 'um/control/stash/cstash_mod.F90'),
		Include(science_root / 'um/control/stash/profilename_length_mod.F90'),
		Include(science_root / 'um/control/stash/set_levels_list.F90'),
		Include(science_root / 'um/control/stash/set_pseudo_list.F90'),
		Include(science_root / 'um/control/stash/stash_array_mod.F90'),
		Include(science_root / 'um/control/stash/stparam_mod.F90'),
		Include(science_root / 'um/control/stash/um_stashcode_mod.F90'),
		Include(science_root / 'um/control/top_level/atm_fields_bounds_mod.F90'),
		Include(science_root / 'um/control/top_level/atm_fields_mod.F90'),
		Include(science_root / 'um/control/top_level/atm_step_local_mod.F90'),
		Include(science_root / 'um/control/top_level/atmos_physics2_alloc.F90'),
		Include(science_root / 'um/control/top_level/atmos_physics2_save_restore.F90'),
		Include(science_root / 'um/control/top_level/cderived_mod.F90'),
		Include(science_root / 'um/control/top_level/errormessagelength_mod.F90'),
		Include(science_root / 'um/control/top_level/filenamelength_mod.F90'),
		Include(science_root / 'um/control/top_level/gen_phys_inputs_mod.F90'),
		Include(science_root / 'um/control/top_level/missing_data_mod.F90'),
		Include(science_root / 'um/control/top_level/model_domain_mod.F90'),
		Include(science_root / 'um/control/top_level/model_time_mod.F90'),
		Include(science_root / 'um/control/top_level/nlstcall_nrun_as_crun_mod.F90'),
		Include(science_root / 'um/control/top_level/submodel_mod.F90'),
		Include(science_root / 'um/control/top_level/timestep_mod.F90'),
		Include(science_root / 'um/control/top_level/tuning_segments_mod.F90'),
		Include(science_root / 'um/control/top_level/var_end_mod.F90'),
		Include(science_root / 'um/control/top_level/version_mod.F90'),
		Include(science_root / 'um/control/top_level/wtrac_atm_step.F90'),
		Include(science_root / 'um/control/ukca_interface/atmos_ukca_callback_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/atmos_ukca_humidity_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/get_emdiag_stash_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_d1_defs.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_nmspec_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_option_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_radaer_lut_in.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_radaer_read_precalc.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_radaer_struct_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_scavenging_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_tracer_stash.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_um_legacy_mod.F90'),
		Include(science_root / 'um/control/ukca_interface/ukca_volcanic_so2.F90'),
		Include(science_root / 'um/scm/modules/s_scmop_mod.F90'),
		Include(science_root / 'um/scm/modules/scm_convss_dg_mod.F90'),
		Include(science_root / 'um/scm/modules/scmoptype_defn.F90'),
		Include(science_root / 'um/scm/stub/dgnstcs_glue_conv.F90'),
		Include(science_root / 'um/scm/stub/scmoutput_stub.F90'),
		Include(science_root / 'um/utility/qxreconf/calc_fit_fsat.F90'),

        Exclude(science_root / 'jules'),
        Include(science_root / 'jules/control/shared'),
        Include(science_root / 'jules/control/lfric'),
        Include(science_root / 'jules/control/cable/shared'),
        Include(science_root / 'jules/control/cable/cable_land'),
        Include(science_root / 'jules/control/cable/interface'),
        Include(science_root / 'jules/control/cable/util'),
        Include(science_root / 'jules/params/cable'),
        Include(science_root / 'jules/science_cable'),
        Include(science_root / 'jules/util/cable'),
        Include(science_root / 'jules/initialisation/cable'),
        Include(science_root / 'jules/control/standalone/jules_fields_mod.F90'),
        Include(science_root / 'jules/util/shared/gridbox_mean_mod.F90'),
        Include(science_root / 'jules/util/shared/metstats/metstats_mod.F90'),
        Include(science_root / 'jules/initialisation/shared/allocate_jules_arrays.F90'),
        Include(science_root / 'jules/initialisation/shared/freeze_soil.F90'),
        Include(science_root / 'jules/initialisation/shared/calc_urban_aero_fields_mod.F90'),
        Include(science_root / 'jules/initialisation/shared/check_compatible_options_mod.F90'),
        Include(science_root / 'jules/science/deposition'),
        Include(science_root / 'jules/science/params'),
        Include(science_root / 'jules/science/radiation'),
        Include(science_root / 'jules/science/snow'),
        Include(science_root / 'jules/science/soil'),
        Include(science_root / 'jules/science/surface'),
        Include(science_root / 'jules/science/vegetation'),

        Exclude(science_root / 'socrates'),
        #Include(science_root / 'socrates/radiance_core'),
        #Include(science_root / 'socrates/interface_core'),
        #Include(science_root / 'socrates/illumination'),
        #Include(science_root / 'socrates/cosp_control/cosp_constants_mod.F90'),                               # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_def_diag.F90'),                                    # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_diagnostics_mod.F90'),                             # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_input_mod.F90'),                                   # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_mod.F90'),                                         # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_radiation_mod.F90'),                               # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_types_mod.F90'),                                   # DRL
        #Include(science_root / 'socrates/cosp_github/driver/src/cosp2_io.f90'),                               # DRL
        #Include(science_root / 'socrates/cosp_github/model-interface/cosp_errorHandling.F90'),                # DRL
        #Include(science_root / 'socrates/cosp_github/model-interface/cosp_kinds.F90'),                        # DRL
        #Include(science_root / 'socrates/cosp_github/src'),                                                   # DRL
        #Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/cosp_optics.F90'),   # DRL
        #Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/quickbeam_optics'),  # DRL
        Include(science_root / 'socrates/cosp_control/cosp_constants_mod.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_def_diag.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_diagnostics_mod.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_input_mod.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_mod.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_radiation_mod.F90'),
        Include(science_root / 'socrates/cosp_control/cosp_types_mod.F90'),
        Include(science_root / 'socrates/cosp_github/driver/src/cosp2_io.f90'),
        Include(science_root / 'socrates/cosp_github/model-interface/cosp_errorHandling.F90'),
        Include(science_root / 'socrates/cosp_github/model-interface/cosp_kinds.F90'),
        Include(science_root / 'socrates/cosp_github/src'),
        Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/cosp_optics.F90'),
        Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/quickbeam_optics'),
        Include(science_root / 'socrates/illumination/astro_constants_mod.F90'),
        Include(science_root / 'socrates/illumination/def_orbit.F90'),
        Include(science_root / 'socrates/illumination/orbprm_mod.F90'),
        Include(science_root / 'socrates/illumination/socrates_illuminate.F90'),
        Include(science_root / 'socrates/illumination/solang_mod.F90'),
        Include(science_root / 'socrates/illumination/solinc_mod.F90'),
        Include(science_root / 'socrates/illumination/solpos_mod.F90'),
        Include(science_root / 'socrates/interface_core/socrates_bones.F90'),
        Include(science_root / 'socrates/interface_core/socrates_cloud_abs_diag.F90'),
        Include(science_root / 'socrates/interface_core/socrates_cloud_ext_diag.F90'),
        Include(science_root / 'socrates/interface_core/socrates_cloud_gen.F90'),
        Include(science_root / 'socrates/interface_core/socrates_cloud_level_diag.F90'),
        Include(science_root / 'socrates/interface_core/socrates_def_diag.F90'),
        Include(science_root / 'socrates/interface_core/socrates_runes.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_aer.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_atm.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_bound.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_cld.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_cld_dim.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_cld_mcica.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_control.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_diag.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_dimen.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_spectrum.F90'),
        Include(science_root / 'socrates/interface_core/socrates_set_topography.F90'),
        Include(science_root / 'socrates/radiance_core/adjust_ir_radiance.F90'),
        Include(science_root / 'socrates/radiance_core/aggregate_cloud.F90'),
        Include(science_root / 'socrates/radiance_core/augment_channel_mod.F90'),
        Include(science_root / 'socrates/radiance_core/augment_radiance.F90'),
        Include(science_root / 'socrates/radiance_core/augment_tiled_radiance.F90'),
        Include(science_root / 'socrates/radiance_core/band_solver.F90'),
        Include(science_root / 'socrates/radiance_core/build_sph_matrix.F90'),
        Include(science_root / 'socrates/radiance_core/calc_actinic_flux_mod.F90'),
        Include(science_root / 'socrates/radiance_core/calc_brdf.F90'),
        Include(science_root / 'socrates/radiance_core/calc_cg_coeff.F90'),
        Include(science_root / 'socrates/radiance_core/calc_contrib_func.F90'),
        Include(science_root / 'socrates/radiance_core/calc_flux_ipa.F90'),
        Include(science_root / 'socrates/radiance_core/calc_gauss_weight_90.F90'),
        Include(science_root / 'socrates/radiance_core/calc_photolysis_incr_mod.F90'),
        Include(science_root / 'socrates/radiance_core/calc_radiance_ipa.F90'),
        Include(science_root / 'socrates/radiance_core/calc_surf_rad.F90'),
        Include(science_root / 'socrates/radiance_core/calc_top_rad.F90'),
        Include(science_root / 'socrates/radiance_core/calc_uplm_sol.F90'),
        Include(science_root / 'socrates/radiance_core/calc_uplm_zero.F90'),
        Include(science_root / 'socrates/radiance_core/cg_kappa_ms.F90'),
        Include(science_root / 'socrates/radiance_core/check_phf_term.F90'),
        Include(science_root / 'socrates/radiance_core/circumsolar_fraction.F90'),
        Include(science_root / 'socrates/radiance_core/cloud_maxcs_split.F90'),
        Include(science_root / 'socrates/radiance_core/column_solver.F90'),
        Include(science_root / 'socrates/radiance_core/copy_clr_full.F90'),
        Include(science_root / 'socrates/radiance_core/copy_clr_sol.F90'),
        Include(science_root / 'socrates/radiance_core/def_aer.F90'),
        Include(science_root / 'socrates/radiance_core/def_atm.F90'),
        Include(science_root / 'socrates/radiance_core/def_bound.F90'),
        Include(science_root / 'socrates/radiance_core/def_cld.F90'),
        Include(science_root / 'socrates/radiance_core/def_control.F90'),
        Include(science_root / 'socrates/radiance_core/def_dimen.F90'),
        Include(science_root / 'socrates/radiance_core/def_mcica.F90'),
        Include(science_root / 'socrates/radiance_core/def_out.F90'),
        Include(science_root / 'socrates/radiance_core/def_planck.F90'),
        Include(science_root / 'socrates/radiance_core/def_spectrum.F90'),
        Include(science_root / 'socrates/radiance_core/def_spherical_geometry.F90'),
        Include(science_root / 'socrates/radiance_core/def_ss_prop.F90'),
        Include(science_root / 'socrates/radiance_core/diff_albedo_basis.F90'),
        Include(science_root / 'socrates/radiance_core/diff_planck_source_mod.F90'),
        Include(science_root / 'socrates/radiance_core/diffusivity_factor.F90'),
        Include(science_root / 'socrates/radiance_core/eig_sys.F90'),
        Include(science_root / 'socrates/radiance_core/eigenvalue_tri.F90'),
        Include(science_root / 'socrates/radiance_core/eval_uplm.F90'),
        Include(science_root / 'socrates/radiance_core/finalise_photol_incr_mod.F90'),
        Include(science_root / 'socrates/radiance_core/gas_list_pcf.F90'),
        Include(science_root / 'socrates/radiance_core/gas_optical_properties.F90'),
        Include(science_root / 'socrates/radiance_core/gauss_angle.F90'),
        Include(science_root / 'socrates/radiance_core/gaussian_weight_pcf.F90'),
        Include(science_root / 'socrates/radiance_core/grey_opt_prop.F90'),
        Include(science_root / 'socrates/radiance_core/hemi_sph_integ.F90'),
        Include(science_root / 'socrates/radiance_core/increment_rad_cf.F90'),
        Include(science_root / 'socrates/radiance_core/inter_k.F90'),
        Include(science_root / 'socrates/radiance_core/inter_pt.F90'),
        Include(science_root / 'socrates/radiance_core/inter_pt_lookup.F90'),
        Include(science_root / 'socrates/radiance_core/inter_t_lookup.F90'),
        Include(science_root / 'socrates/radiance_core/interp1d.F90'),
        Include(science_root / 'socrates/radiance_core/ir_source.F90'),
        Include(science_root / 'socrates/radiance_core/layer_part_integ.F90'),
        Include(science_root / 'socrates/radiance_core/legendre_mod.F90'),
        Include(science_root / 'socrates/radiance_core/legendre_weight.F90'),
        Include(science_root / 'socrates/radiance_core/map_sub_bands_mod.F90'),
        Include(science_root / 'socrates/radiance_core/mcica_column.F90'),
        Include(science_root / 'socrates/radiance_core/mcica_sample.F90'),
        Include(science_root / 'socrates/radiance_core/mix_app_scat.F90'),
        Include(science_root / 'socrates/radiance_core/mix_column.F90'),
        Include(science_root / 'socrates/radiance_core/mixed_solar_source.F90'),
        Include(science_root / 'socrates/radiance_core/monochromatic_gas_flux.F90'),
        Include(science_root / 'socrates/radiance_core/monochromatic_ir_radiance.F90'),
        Include(science_root / 'socrates/radiance_core/monochromatic_radiance.F90'),
        Include(science_root / 'socrates/radiance_core/monochromatic_radiance_sph.F90'),
        Include(science_root / 'socrates/radiance_core/monochromatic_radiance_tseq.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_aerosol.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_baran_mod.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_fu_phf_mod.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_ice_cloud.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_inhom_corr_cairns.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_pade_2_mod.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_ukca_aerosol.F90'),
        Include(science_root / 'socrates/radiance_core/opt_prop_water_cloud.F90'),
        Include(science_root / 'socrates/radiance_core/overlap_coupled.F90'),
        Include(science_root / 'socrates/radiance_core/planck_flux_band_mod.F90'),
        Include(science_root / 'socrates/radiance_core/prsc_gather_spline.F90'),
        Include(science_root / 'socrates/radiance_core/prsc_opt_prop.F90'),
        Include(science_root / 'socrates/radiance_core/quicksort.F90'),
        Include(science_root / 'socrates/radiance_core/rad_pcf.F90'),
        Include(science_root / 'socrates/radiance_core/radiance_calc.F90'),
        Include(science_root / 'socrates/radiance_core/read_spectrum.F90'),
        Include(science_root / 'socrates/radiance_core/rebin_esft_terms.F90'),
        Include(science_root / 'socrates/radiance_core/rescale_continuum.F90'),
        Include(science_root / 'socrates/radiance_core/rescale_phase_fnc.F90'),
        Include(science_root / 'socrates/radiance_core/rescale_tau_csr.F90'),
        Include(science_root / 'socrates/radiance_core/rescale_tau_omega.F90'),
        Include(science_root / 'socrates/radiance_core/scale_absorb.F90'),
        Include(science_root / 'socrates/radiance_core/scale_wenyi.F90'),
        Include(science_root / 'socrates/radiance_core/ses_rescale_contm.F90'),
        Include(science_root / 'socrates/radiance_core/set_cloud_geometry.F90'),
        Include(science_root / 'socrates/radiance_core/set_cloud_pointer.F90'),
        Include(science_root / 'socrates/radiance_core/set_dirn_weights.F90'),
        Include(science_root / 'socrates/radiance_core/set_level_weights.F90'),
        Include(science_root / 'socrates/radiance_core/set_matrix_pentadiagonal.F90'),
        Include(science_root / 'socrates/radiance_core/set_n_cloud_parameter.F90'),
        Include(science_root / 'socrates/radiance_core/set_n_source_coeff.F90'),
        Include(science_root / 'socrates/radiance_core/set_rad_layer.F90'),
        Include(science_root / 'socrates/radiance_core/set_truncation.F90'),
        Include(science_root / 'socrates/radiance_core/shell_sort.F90'),
        Include(science_root / 'socrates/radiance_core/single_scat_sol.F90'),
        Include(science_root / 'socrates/radiance_core/single_scattering.F90'),
        Include(science_root / 'socrates/radiance_core/single_scattering_all.F90'),
        Include(science_root / 'socrates/radiance_core/sol_scat_cos.F90'),
        Include(science_root / 'socrates/radiance_core/solar_coefficient_basic.F90'),
        Include(science_root / 'socrates/radiance_core/solar_source.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_k_eqv.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_k_eqv_scl.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_one_gas.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_random_overlap.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_random_overlap_resort_rebin.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_ses.F90'),
        Include(science_root / 'socrates/radiance_core/solve_band_without_gas.F90'),
        Include(science_root / 'socrates/radiance_core/solver_homogen_direct.F90'),
        Include(science_root / 'socrates/radiance_core/solver_mix_direct.F90'),
        Include(science_root / 'socrates/radiance_core/solver_mix_direct_hogan.F90'),
        Include(science_root / 'socrates/radiance_core/solver_no_scat.F90'),
        Include(science_root / 'socrates/radiance_core/solver_triple.F90'),
        Include(science_root / 'socrates/radiance_core/solver_triple_app_scat.F90'),
        Include(science_root / 'socrates/radiance_core/solver_triple_hogan.F90'),
        Include(science_root / 'socrates/radiance_core/sph_matrix_solver.F90'),
        Include(science_root / 'socrates/radiance_core/sph_solver.F90'),
        Include(science_root / 'socrates/radiance_core/spherical_path.F90'),
        Include(science_root / 'socrates/radiance_core/spherical_solar_source.F90'),
        Include(science_root / 'socrates/radiance_core/spherical_trans_coeff.F90'),
        Include(science_root / 'socrates/radiance_core/spline_evaluate.F90'),
        Include(science_root / 'socrates/radiance_core/spline_fit.F90'),
        Include(science_root / 'socrates/radiance_core/sum_k.F90'),
        Include(science_root / 'socrates/radiance_core/trans_source_coeff.F90'),
        Include(science_root / 'socrates/radiance_core/triple_column.F90'),
        Include(science_root / 'socrates/radiance_core/triple_solar_source.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff_basic.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff_cloud.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff_fast_lw.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff_region.F90'),
        Include(science_root / 'socrates/radiance_core/two_coeff_region_fast_lw.F90'),
        Include(science_root / 'socrates/radiance_core/two_stream.F90'),

        Exclude(science_root / 'ukca'),
        Include(science_root / 'ukca/science'),
        Include(science_root / 'ukca/control/core'),
        Include(science_root / 'ukca/control/glomap_clim/interface'),

        Exclude(science_root / 'shumlib')
    ]


if __name__ == '__main__':
    lfric_source = lfric_source_config.source_root / 'lfric'
    gpl_utils_source = gpl_utils_source_config.source_root / 'gpl_utils'

    os.environ['PYTHONPATH']=str(lfric_source)+'/infrastructure/build/psyclone:${PYTHONPATH}'

    with BuildConfig(project_label='atm $compiler $two_stage') as state:

        # todo: use different dst_labels because they all go into the same folder,
        #       making it hard to see what came from where?
        # internal dependencies
        grab_folder(state, src=lfric_source / 'infrastructure/source/', dst_label='lfric')
        grab_folder(state, src=lfric_source / 'components/driver/source/', dst_label='lfric')
        grab_folder(state, src=lfric_source / 'components' / 'inventory' / 'source', dst_label='')
        grab_folder(state, src=lfric_source / 'components/science/source/', dst_label='lfric')
        grab_folder(state, src=lfric_source / 'components/lfric-xios/source/', dst_label='lfric', )

        # coupler - oasis component
        grab_folder(state, src=lfric_source / 'components/coupler-oasis/source/', dst_label='lfric')

        # gungho dynamical core
        grab_folder(state, src=lfric_source / 'gungho/source/', dst_label='lfric')

        grab_folder(state, src=lfric_source / 'um_physics/source/', dst_label='lfric')
        grab_folder(state, src=lfric_source / 'socrates/source/', dst_label='lfric')
        grab_folder(state, src=lfric_source / 'jules/source/', dst_label='lfric')

        # UM physics - versions as required by the LFRIC_REVISION in grab_lfric.py

        fcm_export(state, src='fcm:um.xm_tr/src', dst_label='science/um', revision='122243')
        fcm_export(state, src='fcm:jules.xm_tr/src', dst_label='science/jules', revision='27111')
        fcm_export(state, src='fcm:socrates.xm_tr/src', dst_label='science/socrates', revision='1483')
        fcm_export(state, src='fcm:shumlib.xm_tr/', dst_label='science/shumlib', revision='um13.4')
        fcm_export(state, src='fcm:casim.xm_tr/src', dst_label='science/casim', revision='um13.4')
        fcm_export(state, src='fcm:ukca.xm_tr/src', dst_label='science/ukca', revision='2833')

        # DRL: OpenMP fix courtesy of Martin Dix:
        #   https://code.metoffice.gov.uk/trac/um/changeset/121298/
        for file in ("control/top_level/atmos_physics2.F90",
                     "control/grids/p_to_t_vol.F90",
                     "control/grids/p_to_t.F90",
                     "control/grids/p_to_u.F90",
                     "control/grids/p_to_v.F90",
                     "control/grids/u_to_p.F90",
                     "control/grids/v_to_p.F90"):
            warnings.warn(f"SPECIAL MEASURE for {file}: \
                          FAB misses OpenMP depdendency on compute_chunk_size_mod" )
            replace_in_file(state.project_workspace / f"source/science/um/{file}", \
                            r"!\$ USE compute_chunk_size_mod", \
                            r"USE compute_chunk_size_mod")

        # lfric_atm
        grab_folder(state, src=lfric_source / 'lfric_atm/source/', dst_label='lfric')

        # generate more source files in source and source/configuration
        configurator(state,
                     lfric_source=lfric_source,
                     gpl_utils_source=gpl_utils_source,
                     rose_meta_conf=lfric_source / 'lfric_atm/rose-meta/lfric-lfric_atm/HEAD/rose-meta.conf',
                     config_dir=state.source_root / 'lfric/configuration'),

        find_source_files(state, path_filters=file_filtering(state))

        # todo: bundle this in with the preprocessor, for a better ux?
        c_pragma_injector(state)

        preprocess_c(
            state,
            path_flags=[
                AddFlags(match="$source/science/um/*", flags=['-I$relative/include']),
                AddFlags(match="$source/science/shumlib/*", flags=['-I$source/science/shumlib/common/src']),
                AddFlags(match='$source/science/um/controls/c_code/*', flags=[
                    '-I$source/science/um/include/other',
                    '-I$source/science/shumlib/shum_thread_utils/src']),
            ],
        )

        preprocess_fortran(
            state,
            common_flags=['-DRDEF_PRECISION=64', '-DUSE_XIOS', '-DUM_PHYSICS', '-DCOUPLED', '-DUSE_MPI=YES'],
            path_flags=[
                AddFlags(match="$source/science/um/*", flags=['-I$relative/include']),
                AddFlags(match="$source/science/jules/*", flags=['-DUM_JULES', '-I$output']),
                AddFlags(match="$source/science/*", flags=['-DLFRIC']),
            ],
        )

        # todo: put this inside the psyclone step, no need for it to be separate, there's nothing required between them
        preprocess_x90(state, common_flags=['-DUM_PHYSICS', '-DRDEF_PRECISION=64', '-DUSE_XIOS', '-DCOUPLED'])

        #psyclone_transformation = get_psyclone_transformation()
        #print('psyclone transformation: ' + psyclone_transformation)

        psyclone(
            state,
            kernel_roots=[state.build_output / 'lfric' / 'kernel'],
            transformation_script=lfric_source / 'lfric_atm/optimisation/nci-gadi/global.py',
            cli_args=[],
        )

        # todo: do we need this one in here?
        fparser_workaround_stop_concatenation(state)

        analyse(
            state,
            root_symbol='lfric_atm',
            ignore_mod_deps=['netcdf', 'MPI', 'yaxt', 'pfunit_mod', 'xios', 'mod_wait'],
        )

        compile_c(state, common_flags=['-c', '-std=c99'])

        compile_fortran(
            state,
            #common_flags=[
            #    '-c',
            #    '-ffree-line-length-none', '-fopenmp',
            #    '-g',
            #    '-finit-integer=31173', '-finit-real=snan', '-finit-logical=true', '-finit-character=85',
            #    '-fcheck=all', '-ffpe-trap=invalid,zero,overflow',
            #    '-Wall', '-Werror=character-truncation', '-Werror=unused-value', '-Werror=tabs',
            #],
                #'-std=f2008',
                #'-ffree-line-length-none', 
                #'-i8','-r8',
            common_flags=[
                '-c',
                '-fopenmp',
                '-g',
                '-std08',
                '-Wall', '-Werror=conversion', '-Werror=unused-variable', '-Werror=character-truncation',
                '-Werror=unused-value', '-Werror=tabs',
                '-r8',
                '-mcmodel=medium',
                '-traceback',
                '-assume nosource_include',
                '-qopenmp',
                '-O2',
                '-fp-model=precise',
                '-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=64', '-DR_TRAN_PRECISION=64',
                '-DUSE_XIOS', '-DUSE_MPI=YES',
            ]
            #path_flags=[
                #AddFlags('$output/science/*', ['-fdefault-real-8', '-fdefault-double-8']),
                #AddFlags('$output/science/*', ['-i8','-r8','-mcmodel=medium','-std08','-g','-traceback','-assume=nosource_include','-qopenmp','-O2','-fp-model=precise']),
                #AddFlags('$output/science/um/atmosphere/COSP/*', ['-std=gnu']), # DRL
            #]
        )

        archive_objects(state)

        link_exe(
            state,
            linker='mpifort',
            flags=[
                '-lyaxt', '-lyaxt_c', '-lnetcdff', '-lnetcdf', '-lhdf5',  # EXTERNAL_DYNAMIC_LIBRARIES
                '-lxios',  # EXTERNAL_STATIC_LIBRARIES
                '-lstdc++',

                '-fopenmp',
            ],
        )
