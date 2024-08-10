#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''This is an OO basic interface to FAB. It allows the typical LFRic
applications to only modify very few settings to have a working FAB build
script.
'''

import logging
import os
from pathlib import Path

from fab.artefacts import ArtefactSet, SuffixFilter
from fab.steps.analyse import analyse
from fab.steps.find_source_files import find_source_files, Exclude
from fab.steps.psyclone import psyclone, preprocess_x90
from fab.steps.grab.folder import grab_folder
from fab.tools import Category
from fab.util import input_to_output_fpath

from fab_base import FabBase
from lfric_common import configurator, fparser_workaround_stop_concatenation
from rose_picker_tool import get_rose_picker
from templaterator import Templaterator


class LFRicBase(FabBase):
    '''This is the base class for all LFRic FAB scripts.

    :param str name: the name to be used for the workspace. Note that
        the name of the compiler will be added to it.
    :param Optional[str] root_symbol:
    '''
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, root_symbol=None):
        super().__init__(name, root_symbol=root_symbol)

        this_file = Path(__file__)
        # The root directory of the LFRic Core
        self._lfric_core_root = this_file.parents[3]
        # lfric_apps is 'next' to lfric_core
        self._lfric_apps_root = self.lfric_core_root.parent / 'apps'

        self._psyclone_config = (self.config.source_root / 'psyclone_config' /
                                 'psyclone.cfg')

    def define_command_line_options(self, parser=None):
        '''Defines command line options. Can be overwritten by a derived
        class which can provide its own instance (to easily allow for a
        different description).
        :param parser: optional a pre-defined argument parser. If not, a
            new instance will be created.
        :type argparse: Optional[:py:class:`argparse.ArgumentParser`]
        '''
        parser = super().define_command_line_options()

        parser.add_argument(
            '--rose_picker', '-rp', type=str, default="v2.0.0",
            help="Version of rose_picker. Use 'system' to use an installed "
                 "version.")
        parser.add_argument(
            '--profile', '-pro', type=str, default="fast-debug",
            help="Profie mode for compilation, choose from \
                'fast-debug'(default), 'full-debug', 'production'")
        parser.add_argument(
            '--precision', '-pre', type=str, default=None,
            help="Precision for reals, choose from '64', '32', \
                default is R_SOLVER_PRECISION=32 while others are 64")
        return parser

    @property
    def lfric_core_root(self):
        return self._lfric_core_root

    @property
    def lfric_apps_root(self):
        return self._lfric_apps_root

    def define_preprocessor_flags(self):
        '''Top level function that sets preprocessor flags
        by calling self.set_flags
        '''
        if self._args.precision:
            precision_flags = ['-DRDEF_PRECISION=' + self._args.precision,
                               '-DR_SOLVER_PRECISION=' + self._args.precision,
                               '-DR_TRAN_PRECISION=' + self._args.precision,
                               '-DR_BL_PRECISION=' + self._args.precision]
        else:
            precision_flags = []
            r_def_precision = os.environ.get("RDEF_PRECISION")
            r_solver_precision = os.environ.get("R_SOLVER_PRECISION")
            r_tran_precision = os.environ.get("R_TRAN_PRECISION")
            r_bl_precision = os.environ.get("R_BL_PRECISION")

            if r_def_precision:
                precision_flags += ['-DRDEF_PRECISION='+r_def_precision]
            else:
                precision_flags += ['-DRDEF_PRECISION=64']

            if r_solver_precision:
                precision_flags += ['-DR_SOLVER_PRECISION='+r_solver_precision]
            else:
                precision_flags += ['-DR_SOLVER_PRECISION=32']

            if r_tran_precision:
                precision_flags += ['-DR_TRAN_PRECISION='+r_tran_precision]
            else:
                precision_flags += ['-DR_TRAN_PRECISION=64']

            if r_bl_precision:
                precision_flags += ['-DR_BL_PRECISION='+r_bl_precision]
            else:
                precision_flags += ['-DR_BL_PRECISION=64']

        # build/tests.mk - for mpi unit tests
        mpi_tests_flags = ['-DUSE_MPI=YES']

        self.set_flags(precision_flags+['-DUSE_XIOS'],
                       self._preprocessor_flags)
        # -DUSE_XIOS is not found in makefile but in fab run_config and
        # driver_io_mod.F90

    def define_compiler_flags(self):
        '''Top level function that sets (compiler- and site-specific)
        compiler flags by calling self.set_flags
        '''
        compiler = super().define_compiler_flags()

        if compiler.suite in ["joerg", "gnu"]:
            flags = []
            # Support Joerg's build environment
            if compiler.suite == "joerg":
                flags.extend(
                    [
                     # The lib directory contains mpi.mod
                     '-I', ('/home/joerg/work/spack/var/spack/environments/'
                            'lfric-v0/.spack-env/view/lib'),
                     # mod_wait.mod
                     '-I', ('/home/joerg/work/spack/var/spack/environments/'
                            'lfric-v0/.spack-env/view/include'),
                     ])
            self.set_flags(flags, self._compiler_flags)
        else:
            raise RuntimeError(f"Unknown compiler suite '{compiler.suite}'.")

    def define_linker_flags(self):
        '''Top level function that sets (site-specific) linker flags
        by calling self.set_flags.
        '''
        # The link flags will depend on the compiler, so use the compiler
        # to set the flags.
        compiler = super().define_linker_flags()

        if compiler.suite == "intel-classic":
            self.set_flags(
                ['-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'], self._link_flags)

        elif compiler.suite == "joerg":
            self.set_flags(
                ['-L', ('/home/joerg/work/spack/var/spack/environments/'
                        'lfric-v0/.spack-env/view/lib'),
                 '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff', '-lnetcdf',
                 '-lhdf5', '-lstdc++'], self._link_flags)
        elif compiler.suite == "gnu":
            self.set_flags(
                ['-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'], self._link_flags)
        else:
            raise RuntimeError(f"Unknown compiler suite '{compiler.suite}'.")

    def grab_files(self):
        dirs = ['infrastructure/source/',
                'components/driver/source/',
                'components/inventory/source/',
                'components/science/source/',
                'components/lfric-xios/source/',
                ]

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_core_root / dir,
                        dst_label='')

        # Copy the PSyclone Config file into a separate directory
        dir = "etc"
        grab_folder(self.config, src=self.lfric_core_root / dir,
                    dst_label='psyclone_config')

        # Get the implementation of the PSyData API for profiling when using
        # TAU. wget requires internet, which gitlab runner does not have.
        # So I temporarily store the tau_psy.f90 in this repo under
        # `infrastructure/source/psydata``. During the install stage, this
        # folder will be copied to lfric_core checkout.
        # tau_psy.f90 will therefore be grabbed when `infrastructure/source``
        # is grabbed.
        # compiler = self.config.tool_box[Category.FORTRAN_COMPILER]
        # linker = self.config.tool_box[Category.LINKER]
        # if "tau_f90.sh" in [compiler.exec_name, linker.exec_name]:
        #     _dst = self.config.source_root / 'psydata'
        #     if not _dst.is_dir():
        #         _dst.mkdir(parents=True)
        #     wget = Tool("wget", "wget")
        #     wget.run(additional_parameters=['-N',
        #                   'https://raw.githubusercontent.com/stfc/PSyclone/'
        #                   'master/lib/profiling/tau/tau_psy.f90'],
        #                   cwd=_dst)

    def find_source_files(self, path_filters=None):
        self.configurator()

        if path_filters is None:
            path_filters = []
        find_source_files(self.config,
                          path_filters=([Exclude('unit-test', '/test/')] +
                                        path_filters))

        self.templaterator(self.config)

    def configurator(self):
        rose_meta = self.get_rose_meta()
        if rose_meta:
            # Get the right version of rose-picker, depending on
            # command line option (defaulting to v2.0.0)
            # TODO: Ideally we would just put this into the toolbox,
            # but atm we can't put several tools of one category in
            # (so ToolBox will need to support more than one MISC tool)
            rp = get_rose_picker(self._args.rose_picker)
            # Ideally we would want to get all source files created in
            # the build directory, but then we need to know the list of
            # files to add them to the list of files to process
            configurator(self.config, lfric_core_source=self.lfric_core_root,
                         lfric_apps_source=self.lfric_apps_root,
                         rose_meta_conf=rose_meta,
                         rose_picker=rp)

    def templaterator(self, config):
        base_dir = self.lfric_core_root / "infrastructure" / "build" / "tools"

        templaterator = Templaterator(base_dir/"Templaterator")
        config.artefact_store["template_files"] = set()
        t90_filter = SuffixFilter(ArtefactSet.INITIAL_SOURCE, [".t90", ".T90"])
        template_files = t90_filter(config.artefact_store)
        # Don't bother with parallelising this, atm there is only one file:
        print("TEMPLATE", template_files)
        for template_file in template_files:
            out_dir = input_to_output_fpath(config=config,
                                            input_path=template_file).parent
            print("OUTDIR IS", out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            templ_r32 = {"kind": "real32", "type": "real"}
            templ_r64 = {"kind": "real64", "type": "real"}
            templ_i32 = {"kind": "int32", "type": "integer"}
            for key_values in [templ_r32, templ_r64, templ_i32]:
                out_file = out_dir / f"field_{key_values['kind']}_mod.f90"
                templaterator.run(template_file, out_file,
                                  key_values=key_values)
                config.artefact_store.add(ArtefactSet.FORTRAN_BUILD_FILES,
                                          out_file)

    def get_rose_meta(self):
        return ""

    def analyse(self):
        self.preprocess_x90()
        self.psyclone()
        fparser_workaround_stop_concatenation(self.config)
        analyse(self.config, root_symbol=self._root_symbol,
                ignore_mod_deps=['netcdf', 'MPI', 'yaxt', 'pfunit_mod',
                                 'xios', 'mod_wait'])

    def preprocess_x90(self):
        preprocess_x90(self.config, common_flags=self._preprocessor_flags)

    def psyclone(self):
        psyclone_cli_args = self.get_psyclone_config()
        compiler = self.config.tool_box[Category.FORTRAN_COMPILER]
        linker = self.config.tool_box.get_tool(Category.LINKER,
                                               mpi=self.config.mpi)
        if "tau_f90.sh" in [compiler.exec_name, linker.exec_name]:
            psyclone_cli_args.extend(self.get_psyclone_profiling_option())

        psyclone(self.config, kernel_roots=[self.config.build_output],
                 transformation_script=self.get_transformation_script,
                 api="dynamo0.3",
                 cli_args=psyclone_cli_args)

    def get_psyclone_config(self):
        return ["--config", self._psyclone_config]

    def get_psyclone_profiling_option(self):
        return ["--profile", "kernels"]

    def get_transformation_script(self, fpath, config):
        ''':returns: the transformation script to be used by PSyclone.
        :rtype: Path
        '''
        optimisation_path = config.source_root / 'optimisation' / 'nci-gadi'
        relative_path = None
        for base_path in [config.source_root, config.build_output]:
            try:
                relative_path = fpath.relative_to(base_path)
            except ValueError:
                pass
        if relative_path:
            local_transformation_script = (optimisation_path /
                                           (relative_path.with_suffix('.py')))
            if local_transformation_script.exists():
                return local_transformation_script

        global_transformation_script = optimisation_path / 'global.py'
        if global_transformation_script.exists():
            return global_transformation_script
        return ""


# ==========================================================================
if __name__ == "__main__":

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    lfric_base = LFRicBase(name="command-line-test",
                           root_symbol=None)
