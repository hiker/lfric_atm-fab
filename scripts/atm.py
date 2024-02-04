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
        Include(science_root / 'um/atmosphere/aerosols'),
        Include(science_root / 'um/atmosphere/atmosphere_service'),
        Include(science_root / 'um/atmosphere/boundary_layer'),
        Include(science_root / 'um/atmosphere/carbon/carbon_options_mod.F90'),
        Include(science_root / 'um/atmosphere/convection'),
        Include(science_root / 'um/atmosphere/convection/comorph/control/comorph_constants_mod.F90'),
        Include(science_root / 'um/atmosphere/diffusion_and_filtering/leonard_incs_mod.F90'),
        Include(science_root / 'um/atmosphere/diffusion_and_filtering/turb_diff_ctl_mod.F90'),
        Include(science_root / 'um/atmosphere/diffusion_and_filtering/turb_diff_mod.F90'),
        Include(science_root / 'um/atmosphere/dynamics'),
        Include(science_root / 'um/atmosphere/dynamics_advection'),
        Include(science_root / 'um/atmosphere/electric'),
        Include(science_root / 'um/atmosphere/energy_correction/eng_corr_inputs_mod.F90'),
        Include(science_root / 'um/atmosphere/energy_correction/flux_diag-fldiag1a.F90'),
        Include(science_root / 'um/atmosphere/free_tracers/free_tracers_inputs_mod.F90'),
        Include(science_root / 'um/atmosphere/free_tracers/water_tracers_mod.F90'),
        Include(science_root / 'um/atmosphere/free_tracers/wtrac_all_phase_chg.F90'),
        Include(science_root / 'um/atmosphere/free_tracers/wtrac_calc_ratio.F90'),
        Include(science_root / 'um/atmosphere/free_tracers/wtrac_move_phase.F90'),
        Include(science_root / 'um/atmosphere/idealised'),
        Include(science_root / 'um/atmosphere/large_scale_cloud'),
        Include(science_root / 'um/atmosphere/large_scale_precipitation'),
        Include(science_root / 'um/atmosphere/PWS_diagnostics/pws_diags_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/def_easyaerosol.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/easyaerosol_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/easyaerosol_option_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/easyaerosol_read_input_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/fsd_parameters_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/max_calls.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/r2_calc_total_cloud_cover.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/rad_input_mod.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/solinc_data.F90'),
        Include(science_root / 'um/atmosphere/radiation_control/spec_sw_lw.F90'),
        Include(science_root / 'um/atmosphere/stochastic_physics/stochastic_physics_run_mod.F90'),
        Include(science_root / 'um/atmosphere/tracer_advection/trsrce-trsrce2a.F90'),
        Include(science_root / 'um/control/dummy_libs/drhook/parkind1.F90'),
        Include(science_root / 'um/control/dummy_libs/drhook/yomhook.F90'),
        Include(science_root / 'um/control/glomap_clim_interface/glomap_clim_option_mod.F90'),
        Include(science_root / 'um/control/grids'),
        Include(science_root / 'um/control/misc'),
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
        Include(science_root / 'um/control/top_level'),
        Include(science_root / 'um/control/ukca_interface/atmos_ukca_callback_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/atmos_ukca_humidity_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/get_emdiag_stash_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_d1_defs.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_dissoc.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_eg_tracers_total_mass_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_nmspec_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_option_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_photo_scheme_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_radaer_lut_in.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_radaer_read_precalc.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_radaer_read_presc_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_radaer_struct_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_scavenging_diags_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_scavenging_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_tracer_stash.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_um_legacy_mod.F90'),
        Include(science_root / 'um/control/ukca_interface/ukca_volcanic_so2.F90'),
        Include(science_root / 'um/scm/modules/scmoptype_defn.F90'),
        Include(science_root / 'um/scm/modules/s_scmop_mod.F90'),
        Include(science_root / 'um/scm/modules/scm_convss_dg_mod.F90'),
        Include(science_root / 'um/scm/stub/dgnstcs_glue_conv.F90'),
        Include(science_root / 'um/scm/stub/scmoutput_stub.F90'),
        #Include(science_root / 'um/atmosphere/COSP/cosp_input_mod.F90'),
        #Include(science_root / 'um/atmosphere/COSP/cosp.F90'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2/model-interface'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2/source/cosp_config.F90'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2/cosp_constants_mod.F90'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2/cosp_utils_mod.F90'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2/cosp_types_mod.F90'), # DRL
        #Include(science_root / 'um/atmosphere/COSP'), # DRL
        #Include(science_root / 'um/atmosphere/COSP2'), # DRL
        Include(science_root / 'um/control/coupling'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/g_wave_input_mod.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_prec_mod.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_params_mod.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_core_mod.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_ussp_mod.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_block.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_wave.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/gw_setup.F90'),
        Include(science_root / 'um/atmosphere/gravity_wave_drag/c_gwave_mod.F90'),
        Include(science_root / 'um/utility/qxreconf/calc_fit_fsat.F'),

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
        Include(science_root / 'socrates/radiance_core'),
        Include(science_root / 'socrates/interface_core'),
        Include(science_root / 'socrates/illumination'),
        #Include(science_root / 'socrates/cosp_control'), # DRL
        #Include(science_root / 'socrates/cosp_control/cosp_mod.F90'), # DRL
        #Include(science_root / 'socrates/cosp_github/model-interface'), # DRL
        #Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/quickbeam_optics'), # DRL
        Include(science_root / 'socrates/cosp_control/cosp_constants_mod.F90'),                               # DRL
        Include(science_root / 'socrates/cosp_control/cosp_def_diag.F90'),                                    # DRL
        Include(science_root / 'socrates/cosp_control/cosp_diagnostics_mod.F90'),                             # DRL
        Include(science_root / 'socrates/cosp_control/cosp_input_mod.F90'),                                   # DRL
        Include(science_root / 'socrates/cosp_control/cosp_mod.F90'),                                         # DRL
        Include(science_root / 'socrates/cosp_control/cosp_radiation_mod.F90'),                               # DRL
        Include(science_root / 'socrates/cosp_control/cosp_types_mod.F90'),                                   # DRL
        Include(science_root / 'socrates/cosp_github/driver/src/cosp2_io.f90'),                               # DRL
        Include(science_root / 'socrates/cosp_github/model-interface/cosp_errorHandling.F90'),                # DRL
        Include(science_root / 'socrates/cosp_github/model-interface/cosp_kinds.F90'),                        # DRL
        Include(science_root / 'socrates/cosp_github/src'),                                                   # DRL
        Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/cosp_optics.F90'),   # DRL
        Include(science_root / 'socrates/cosp_github/subsample_and_optics_example/optics/quickbeam_optics'),  # DRL

        Exclude(science_root / 'ukca'),
        Include(science_root / 'ukca/science'),
        Include(science_root / 'ukca/control/core'),
        Include(science_root / 'ukca/control/glomap_clim/interface'),

        Exclude(science_root / 'shumlib')

    ]


if __name__ == '__main__':
    lfric_source = lfric_source_config.source_root / 'lfric'
    gpl_utils_source = gpl_utils_source_config.source_root / 'gpl_utils'

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

        fcm_export(state, src='fcm:um.xm_tr/src', dst_label='science/um', revision='vn13.4')
        fcm_export(state, src='fcm:jules.xm_tr/src', dst_label='science/jules', revision='um13.4')
        fcm_export(state, src='fcm:socrates.xm_tr/src', dst_label='science/socrates', revision='um13.4')
        fcm_export(state, src='fcm:shumlib.xm_tr/', dst_label='science/shumlib', revision='um13.4')
        fcm_export(state, src='fcm:casim.xm_tr/src', dst_label='science/casim', revision='um13.4')
        fcm_export(state, src='fcm:ukca.xm_tr/src', dst_label='science/ukca', revision='um13.4')
        #fcm_export(state, src='fcm:um.xm_tr/src', dst_label='science/um', revision='119527')
        #fcm_export(state, src='fcm:jules.xm_tr/src', dst_label='science/jules', revision='um13.3')
        #fcm_export(state, src='fcm:socrates.xm_tr/src', dst_label='science/socrates', revision='um13.3')
        #fcm_export(state, src='fcm:shumlib.xm_tr/', dst_label='science/shumlib', revision='um13.3')
        #fcm_export(state, src='fcm:casim.xm_tr/src', dst_label='science/casim', revision='10515')
        #fcm_export(state, src='fcm:ukca.xm_tr/src', dst_label='science/ukca', revision='um13.3')

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
        # DRL: additional fixes
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/math_lib.f90", \
        #                r"USE m_mrgrnk, ONLY: mrgrnk", \
        #                r"USE m_mrgrnk, ONLY: R_mrgrnk")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/math_lib.f90", \
        #                r"  CALL mrgrnk(s(i1:i2),idx)", \
        #                r"  CALL R_mrgrnk(s(i1:i2),idx)")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/math_lib.f90", \
        #                r"CONTAINS", \
        #                r"CONTAINS\nPROCEDURE, PUBLIC :: gammac")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/array_lib.f90", \
        #                r"USE m_mrgrnk, ONLY: mrgrnk", \
        #                r"USE m_mrgrnk, ONLY: R_mrgrnk")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/array_lib.f90", \
        #                r"  CALL mrgrnk(list,idx)", \
        #                r"  CALL R_mrgrnk(list,idx)")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/array_lib.f90", \
        #                r"CALL mrgrnk(xarr,idx)", \
        #                r"CALL R_mrgrnk(xarr,idx)")
        #replace_in_file(state.project_workspace / "source/science/um/atmosphere/COSP/quickbeam/mrgrnk.f90", \
        #                r"PUBLIC :: mrgrnk", \
        #                r"PROCEDURE, PUBLIC :: mrgrnk")

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