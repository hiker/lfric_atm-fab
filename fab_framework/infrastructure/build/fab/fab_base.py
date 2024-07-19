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

import argparse
from importlib import import_module
import logging
import os
from pathlib import Path
import sys

from fab.artefacts import ArtefactSet, SuffixFilter
from fab.build_config import BuildConfig
from fab.steps.analyse import analyse
from fab.steps.archive_objects import archive_objects
from fab.steps.c_pragma_injector import c_pragma_injector
from fab.steps.compile_c import compile_c
from fab.steps.compile_fortran import compile_fortran
from fab.steps.find_source_files import find_source_files, Exclude
from fab.steps.link import link_exe
from fab.steps.preprocess import preprocess_c, preprocess_fortran
from fab.steps.psyclone import psyclone, preprocess_x90
from fab.steps.grab.folder import grab_folder
from fab.tools import Category, ToolBox, ToolRepository
from fab.util import input_to_output_fpath

from lfric_common import configurator, fparser_workaround_stop_concatenation
from rose_picker_tool import get_rose_picker
from templaterator import Templaterator


logger = logging.getLogger('fab')
logger.setLevel(logging.DEBUG)


class FabBase:
    '''This is the base class for all LFRic FAB scripts.

    :param str name: the name to be used for the workspace. Note that
        the name of the compiler will be added to it.
    :param Optional[str] root_symbol:
    '''
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, root_symbol=None):
        self._site = None
        self._platform = None
        self._target = None
        # We have to determine the site-specific setup first, so that e.g.
        # new compilers can be added before command line options are handled
        # (which might request this new compiler). So first parse the command
        # line for --site and --platform only:
        self.define_site_platform_target()

        # Now that site, platform and target are defined, import any
        # site-specific settings
        self.site_specific_setup()

        # Define the tool box, which might be started to be filled
        # when handling command line options:
        self._tool_box = ToolBox()
        parser = self.define_command_line_options()
        self.handle_command_line_options(parser)

        self._site_config.update_toolbox(self._tool_box)
        this_file = Path(__file__)
        # The root directory of the LFRic Core installation
        self._lfric_core_root = this_file.parents[3]

        if root_symbol:
            self._root_symbol = root_symbol
        else:
            self._root_symbol = name

        # lfric_apps is 'next' to lfric_core
        self._lfric_apps_root = self.lfric_core_root.parent / 'apps'

        self._config = BuildConfig(tool_box=self._tool_box,
                                   project_label=f'{name}-$compiler',
                                   verbose=True,
                                   n_procs=16,
                                   )
        self._preprocessor_flags = []
        self._compiler_flags = []
        self._link_flags = []
        self._psyclone_config = (self._config.source_root / 'psyclone_config' /
                                 'psyclone.cfg')
        self.define_preprocessor_flags()
        self.define_compiler_flags()
        self.define_linker_flags()

    def define_preprocessor_flags(self):
        '''Top level function that sets preprocessor flags
        by calling self.set_preprocessor_flags
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

        self.set_preprocessor_flags(precision_flags+['-DUSE_XIOS'])
        # -DUSE_XIOS is not found in makefile but in fab run_config and
        # driver_io_mod.F90

    def define_site_platform_target(self):
        '''This method defines the attributes site, platform (and
        target=site-platform) based on the command line option --site
        and --platform (using $SITE and $PLATFORM as a default). If
        site or platform is missing and the corresponding environment
        variable is not set, 'default' will be used.
        '''

        # Use `argparser.parse_known_args` to just handle --site and
        # --platform. We also suppress help (all of which will be handled
        # later, including proper help messages)
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--site", "-s", type=str, default="$SITE")
        parser.add_argument("--platform", "-p", type=str, default="$PLATFORM")

        args = parser.parse_known_args()[0]   # Ignore element [1]=unknown args
        if args.site == "$SITE":
            self._site = os.environ.get("SITE", "default")
        elif args.site:
            self._site = args.site
        else:
            self._site = "default"

        if args.platform == "$PLATFORM":
            self._platform = os.environ.get("PLATFORM", "default")
        elif args.platform:
            self._platform = args.platform
        else:
            self._platform = "default"

        # Define target attribute for site&platform-specific files
        self._target = f"{self._site}_{self._platform}"

    def site_specific_setup(self):
        '''Imports a site-specific config file. The location is based
        on the attribute target (which is set to be site-platform).
        '''
        try:
            config_module = import_module(f"{self.target}.config")
        except ModuleNotFoundError:
            # We log a warning, but proceed, since there is no need to
            # have a site-specific file.
            logger.warning(f"Cannot find site-specific module "
                           f"'{self.target}.config'.")
            self._site_config = None
            return
        print("IMPORTED", self.target)
        # The constructor handles everything.
        self._site_config = config_module.Config()

    def define_compiler_flags(self):
        '''Top level function that sets (compiler- and site-specific)
        compiler flags by calling self.set_compiler_flags
        '''
        compiler = self._tool_box[Category.FORTRAN_COMPILER]
        # TODO: This should go into compiler.get_version() in FAB
        compiler_version_comparison = ''.join(
            f"{int(version_component):02d}"
            for version_component in compiler.get_version().split('.'))

        if compiler.suite == "intel-classic":
            # The flag groups are mainly from infrastructure/build/fortran
            # /ifort.mk
            debug_flags = ['-g', '-traceback']
            no_optimisation_flags = ['-O0']
            safe_optimisation_flags = ['-O2', '-fp-model=strict']
            risky_optimisation_flags = ['-O3', '-xhost']
            openmp_arg_flags = ['-qopenmp']
            warnings_flags = ['-warn all', '-warn errors', '-gen-interfaces',
                              'nosource']
            unit_warnings_flags = ['-warn all', '-gen-interfaces', 'nosource']
            init_flags = ['-ftrapuv']

            # ifort.mk: bad interaction between array shape checking and
            # the matmul" intrinsic in at least some iterations of v19.
            if '190000' <= compiler_version_comparison < '190100':
                runtime_flags = ['-check all,noshape', '-fpe0']
            else:
                runtime_flags = ['-check all', '-fpe0']

            # ifort.mk: option for checking code meets Fortran standard
            # - currently 2008
            fortran_standard_flags = ['-stand f08']

            # ifort.mk has some app and file-specific options for older
            # intel compilers. They have not been included here
            compiler_flag_group = openmp_arg_flags

            if self._args.profile == 'full-debug':
                compiler_flag_group += (debug_flags + warnings_flags +
                                        init_flags + runtime_flags +
                                        no_optimisation_flags +
                                        fortran_standard_flags)
            elif self._args.profile == 'production':
                compiler_flag_group += (debug_flags + warnings_flags +
                                        risky_optimisation_flags)
            else:  # 'fast-debug'
                compiler_flag_group += (debug_flags + warnings_flags +
                                        safe_optimisation_flags +
                                        fortran_standard_flags)

            self.set_compiler_flags(compiler_flag_group)

        elif compiler.suite in ["joerg", "gnu"]:
            flags = ['-ffree-line-length-none', '-fopenmp', '-g',
                     '-Werror=character-truncation', '-Werror=unused-value',
                     '-Werror=tabs', '-fdefault-real-8', '-fdefault-double-8',
                     ]
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
            self.set_compiler_flags(flags)
        else:
            raise RuntimeError(f"Unknown compiler suite '{compiler.suite}'.")

    def define_linker_flags(self):
        '''Top level function that sets (site-specific) linker flags
        by calling self.set_link_flags.
        '''
        # The link flags will depend on the compiler, so use the compiler
        # to set the flags.
        compiler = self._tool_box[Category.FORTRAN_COMPILER]

        # TODO: Unfortunately, for now we have to set openmp flags explicitly
        # for linker. For now, all compiler flags are still set in the compile
        # step only, so the linker (which adds compiler flags from the
        # compiler instance) does not have these flags. Once the flags are
        # moved from the compile step into the compiler object, the linker
        # will be able to pick up openmp (and other compiler flags)
        # automatically.
        if compiler.suite == "intel-classic":
            self.set_link_flags(
                ['-qopenmp', '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'])

        elif compiler.suite == "joerg":
            self.set_link_flags(
                ['-fopenmp',
                 '-L', ('/home/joerg/work/spack/var/spack/environments/'
                        'lfric-v0/.spack-env/view/lib'),
                 '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff', '-lnetcdf',
                 '-lhdf5', '-lstdc++'])
        elif compiler.suite == "gnu":
            self.set_link_flags(
                ['-fopenmp', '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'])
        else:
            raise RuntimeError(f"Unknown compiler suite '{compiler.suite}'.")

    def define_command_line_options(self, parser=None):
        '''Defines command line options. Can be overwritten by a derived
        class which can provide its own instance (to easily allow for a
        different description).
        :param parser: optional a pre-defined argument parser. If not, a
            new instance will be created.
        :type argparse: Optional[:py:class:`argparse.ArgumentParser`]
        '''

        if not parser:
            # The formatter class makes sure to print default settings
            parser = argparse.ArgumentParser(
                description=("A FAB-based build system. Note that if --suite "
                             "is specified, this will change the default for "
                             "compiler and linker"),
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument(
            '--suite', '-v', type=str, default=None,
            help="Sets the default suite for compiler and linker")
        parser.add_argument(
            '--fc', '-fc', type=str, default="$FC",
            help="Name of the Fortran compiler to use")
        parser.add_argument(
            '--cc', '-cc', type=str, default="$CC",
            help="Name of the C compiler to use")
        parser.add_argument(
            '--ld', '-ld', type=str, default="$LD",
            help="Name of the linker to use")
        parser.add_argument(
            '--rose_picker', '-rp', type=str, default="v2.0.0",
            help="Version of rose_picker. Use 'system' to use an installed "
                 "version.")
        parser.add_argument("--site", "-s", type=str,
                            default="$SITE or 'default'",
                            help="Name of the site to use.")
        parser.add_argument("--platform", "-p", type=str,
                            default="$PLATFORM or 'default'",
                            help="Name of the platform of the site to use.")
        parser.add_argument(
            '--wrapper_compiler', '-wr_c', type=str, default=None,
            help="Sets a wrapper for compiler")
        parser.add_argument(
            '--wrapper_linker', '-wr_l', type=str, default=None,
            help="Sets a wrapper for linker")
        parser.add_argument(
            '--profile', '-pro', type=str, default="fast-debug",
            help="Profie mode for compilation, choose from \
                'fast-debug'(default), 'full-debug', 'production'")
        parser.add_argument(
            '--precision', '-pre', type=str, default=None,
            help="Precision for reals, choose from '64', '32', \
                default is R_SOLVER_PRECISION=32 while others are 64")
        return parser

    def handle_command_line_options(self, parser):
        '''Analyse the actual command line options using the specified parser.
        The base implementation will handle the `--suite` parameter, and
        compiler/linker parameters (including the usage of environment
        variables). Needs to be overwritten to handle additional options
        specified by a derived script.

        :param parser: the argument parser.
        :type parser: :py:class:`argparse.ArgumentParser`
        '''
        # pylint: disable=too-many-branches
        self._args = parser.parse_args(sys.argv[1:])

        tr = ToolRepository()
        if self._args.suite:
            if self._args.suite == "joerg":
                tr.set_default_compiler_suite("gnu")
            else:
                tr.set_default_compiler_suite(self._args.suite)
            print(f"Setting suite to '{self._args.suite}'.")
            # suite will overwrite use of env variables, so change the
            # value of these arguments to be none so they will be ignored
            if self._args.fc == "$FC":
                self._args.fc = None
            if self._args.cc == "$CC":
                self._args.cc = None
            if self._args.ld == "$LD":
                self._args.ld = None
        else:
            # If no suite is specified, if required set the defaults
            # for compilers based on the environment variables.
            if self._args.fc == "$FC":
                self._args.fc = os.environ.get("FC")
            if self._args.cc == "$CC":
                self._args.cc = os.environ.get("CC")
            if self._args.ld == "$LD":
                self._args.ld = os.environ.get("LD")

        # If no suite was specified, and a special tool was requested,
        # add it to the tool box:
        if self._args.cc:
            cc = tr.get_tool(Category.C_COMPILER, self._args.cc)
            self._tool_box.add_tool(cc)
        if self._args.fc:
            fc = tr.get_tool(Category.FORTRAN_COMPILER, self._args.fc)
            self._tool_box.add_tool(fc)
        if self._args.ld:
            ld = tr.get_tool(Category.LINKER, self._args.ld)
            self._tool_box.add_tool(ld)

        if self._args.wrapper_compiler:
            self._tool_box[Category.C_COMPILER].exec_name = \
                self._args.wrapper_compiler
            self._tool_box[Category.FORTRAN_COMPILER].exec_name = \
                self._args.wrapper_compiler

    @property
    def config(self):
        ''':returns: the FAB BuildConfig instance.
        :rtype: :py:class:`fab.BuildConfig`
        '''
        return self._config

    @property
    def lfric_core_root(self):
        return self._lfric_core_root

    @property
    def lfric_apps_root(self):
        return self._lfric_apps_root

    @property
    def target(self):
        ''':returns: the target (="site-platform").'''
        return self._target

    def set_preprocessor_flags(self, list_of_flags):
        self._preprocessor_flags += list_of_flags

    def set_compiler_flags(self, list_of_flags):
        self._compiler_flags = list_of_flags[:]

    def set_link_flags(self, list_of_flags):
        self._link_flags = list_of_flags[:]

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
        if path_filters is None:
            path_filters = []
        find_source_files(self.config,
                          path_filters=([Exclude('unit-test', '/test/')] +
                                        path_filters))

    def get_rose_meta(self):
        return ""

    def templaterator(self, config):
        base_dir = self.lfric_core_root / "infrastructure" / "build" / "tools"

        templaterator = Templaterator(base_dir/"Templaterator")
        config.artefact_store["template_files"] = set()
        t90_filter = SuffixFilter(ArtefactSet.ALL_SOURCE, [".t90", ".T90"])
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

    def preprocess_c(self, path_flags=None):
        preprocess_c(self.config, common_flags=self._preprocessor_flags,
                     path_flags=path_flags)

    def preprocess_fortran(self, path_flags=None):
        preprocess_fortran(self.config, common_flags=self._preprocessor_flags,
                           path_flags=path_flags)

    def preprocess_x90(self):
        preprocess_x90(self.config, common_flags=self._preprocessor_flags)

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

    def get_psyclone_config(self):
        return ["--config", self._psyclone_config]

    def get_psyclone_profiling_option(self):
        return ["--profile", "kernels"]

    def psyclone(self):
        psyclone_cli_args = self.get_psyclone_config()
        compiler = self.config.tool_box[Category.FORTRAN_COMPILER]
        linker = self.config.tool_box[Category.LINKER]
        if "tau_f90.sh" in [compiler.exec_name, linker.exec_name]:
            psyclone_cli_args.extend(self.get_psyclone_profiling_option())

        psyclone(self.config, kernel_roots=[self.config.build_output],
                 transformation_script=self.get_transformation_script,
                 api="dynamo0.3",
                 cli_args=psyclone_cli_args)

    def analyse(self):
        analyse(self.config, root_symbol=self._root_symbol,
                ignore_mod_deps=['netcdf', 'MPI', 'yaxt', 'pfunit_mod',
                                 'xios', 'mod_wait'])

    def compile_c(self):
        compile_c(self.config)

    def compile_fortran(self, path_flags=None):
        compile_fortran(self.config, common_flags=self._compiler_flags,
                        path_flags=path_flags)

    def archive_objects(self):
        archive_objects(self.config)

    def link(self):
        link_exe(self.config, flags=self._link_flags)

    def build(self):
        # We need to use with to trigger the entrance/exit functionality,
        # but otherwise the config object is used from this object, so no
        # need to use it anywhere.
        with self._config as _:
            self.grab_files()
            # generate more source files in source and source/configuration
            self.configurator()
            self.find_source_files()
            self.templaterator(self.config)
            c_pragma_injector(self.config)
            self.preprocess_c()
            self.preprocess_fortran()
            self.preprocess_x90()
            self.psyclone()
            fparser_workaround_stop_concatenation(self.config)
            self.analyse()
            self.compile_c()
            self.compile_fortran()
            self.archive_objects()
            self.link()


# ==========================================================================
if __name__ == "__main__":
    fab_base = FabBase(name="command-line-test",
                       root_symbol=None)
