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
import logging
import os
from pathlib import Path
import sys

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
from fab.newtools import Categories, Linker, ToolBox, ToolRepository

from lfric_common import configurator, fparser_workaround_stop_concatenation


logger = logging.getLogger('fab')
logger.setLevel(logging.DEBUG)


class FabBase:
    '''This is the base class for all LFRic FAB scripts.

    :param str name: the name to be used for the workspace. Note that
        the name of the compiler will be added to it.
    :param gpl_utils_config: a BuildConfig object which contains the
        path to LFRic's gpl_utils, from which rose-picker is used.
    :param Optional[str] root_symbol:
    '''

    def __init__(self, name, gpl_utils_config, root_symbol=None):
        self._tool_box = ToolBox()
        parser = self.define_command_line_options()
        self.handle_command_line_options(parser)

        this_file = Path(__file__)
        # The root directory of the LFRic Core installation
        self._lfric_core_root = this_file.parents[3]
        if root_symbol:
            self._root_symbol = root_symbol
        else:
            self._root_symbol = name
        self._gpl_utils_source = gpl_utils_config.source_root / 'gpl_utils'
        self._lfric_apps_root = gpl_utils_config.source_root / 'lfric_apps'
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
        self.define_compiler_flags()
        self.define_linker_flags()

    def define_compiler_flags(self):
        '''Top level function that sets (compiler- and site-specific)
        compiler flags by calling self.set_compiler_flags
        '''
        compiler = self._tool_box[Categories.FORTRAN_COMPILER]
        if compiler.vendor == "intel":
            self.set_compiler_flags(
                ['-g', '-r8', '-mcmodel=medium', '-traceback',
                 '-Wall', '-Werror=conversion', '-Werror=unused-variable',
                 '-Werror=character-truncation',
                 '-Werror=unused-value', '-Werror=tabs',
                 '-assume nosource_include',
                 '-qopenmp', '-O2', '-std08', '-fp-model=strict', '-fpe0',
                 '-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=64',
                 '-DR_TRAN_PRECISION=64',
                 '-DUSE_XIOS', '-DUSE_MPI=YES',
                 ])
        elif compiler.vendor in ["joerg", "gnu"]:
            flags = ['-ffree-line-length-none', '-fopenmp', '-g',
                     '-Werror=character-truncation', '-Werror=unused-value',
                     '-Werror=tabs', '-fdefault-real-8', '-fdefault-double-8',
                     ]
            # Support Joerg's build environment
            if compiler.vendor == "joerg":
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
            raise RuntimeError(f"Unknown compiler vendor '{compiler.vendor}'.")

    def define_linker_flags(self):
        '''Top level function that sets (site-specific) linker flags
        by calling self.set_link_flags.
        '''
        # The link flags will depend on the compiler, so use the compiler
        # to set the flags.
        compiler = self._tool_box[Categories.FORTRAN_COMPILER]

        # TODO: Unfortunately, for now we have to set openmp flags explicitly
        # for linker. For now, all compiler flags are still set in the compile
        # step only, so the linker (which adds compiler flags from the
        # compiler instance) does not have these flags. Once the flags are
        # moved from the compile step into the compiler object, the linker
        # will be able to pick up openmp (and other compiler flags)
        # automatically.
        if compiler.vendor == "intel":
            self.set_link_flags(
                ['-qopenmp', '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'])

        elif compiler.vendor == "joerg":
            self.set_link_flags(
                ['-fopenmp',
                 '-L', ('/home/joerg/work/spack/var/spack/environments/'
                        'lfric-v0/.spack-env/view/lib'),
                 '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff', '-lnetcdf',
                 '-lhdf5', '-lstdc++'])
        elif compiler.vendor == "gnu":
            self.set_link_flags(
                ['-fopenmp', '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff',
                 '-lnetcdf', '-lhdf5', '-lstdc++'])
        else:
            raise RuntimeError(f"Unknown compiler vendor '{compiler.vendor}'.")

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
                description=("A FAB-based build system. Note that if --vendor "
                             "is specified, this will change the default for "
                             "compiler and linker"),
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument(
            '--vendor', '-v', type=str, default=None,
            help="Sets the default vendor for compiler and linker")
        parser.add_argument(
            '--fc', '-fc', type=str, default="$FC",
            help="Name of the Fortran compiler to use")
        parser.add_argument(
            '--cc', '-cc', type=str, default="$CC",
            help="Name of the C compiler to use")
        parser.add_argument(
            '--ld', '-ld', type=str, default="$LD",
            help="Name of the linker to use")
        return parser

    def handle_command_line_options(self, parser):
        '''Analyse the actual command line options using the specified parser.
        The base implementation will handle the `--vendor` parameter, and
        compiler/linker parameters (including the usage of environment
        variables). Needs to be overwritten to handle additional options
        specified by a derived script.

        :param parser: the argument parser.
        :type parser: :py:class:`argparse.ArgumentParser`
        '''

        self._args = parser.parse_args(sys.argv[1:])

        tr = ToolRepository()
        if self._args.vendor:
            if self._args.vendor == "joerg":
                tr.set_default_vendor("gnu")
            else:
                tr.set_default_vendor(self._args.vendor)
            print(f"Setting vendor to '{self._args.vendor}'.")
            # Vendor will overwrite use of env variables, so change the
            # value of these arguments to be none so they will be ignored
            if self._args.fc == "$FC":
                self._args.fc = None
            if self._args.cc == "$CC":
                self._args.cc = None
            if self._args.ld == "$LD":
                self._args.ld = None
        else:
            # If no vendor is specified, if required set the defaults
            # for compilers based on the environment variables.
            if self._args.fc == "$FC":
                self._args.fc = os.environ.get("FC")
            if self._args.cc == "$CC":
                self._args.cc = os.environ.get("CC")
            if self._args.ld == "$LD":
                self._args.ld = os.environ.get("LD")

        # If no vendor was specified, and a special tool was requested,
        # add it to the tool box:
        if self._args.cc:
            cc = tr.get_tool(Categories.C_COMPILER, self._args.cc)
            self._tool_box.add_tool(cc)
        if self._args.fc:
            fc = tr.get_tool(Categories.FORTRAN_COMPILER, self._args.fc)
            self._tool_box.add_tool(fc)
        if self._args.ld:
            ld = tr.get_tool(Categories.LINKER, self._args.ld)
            self._tool_box.add_tool(ld)

        fc = self._tool_box[Categories.FORTRAN_COMPILER]
        # A hack for now :(
        if self._args.vendor == "joerg":
            fc = self._tool_box[Categories.FORTRAN_COMPILER]
            fc._vendor = "joerg"

        linker = Linker(exec_name="mpif90", compiler=fc)
        self._tool_box.add_tool(linker)

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
    def gpl_utils_source(self):
        return self._gpl_utils_source

    def set_preprocessor_flags(self, list_of_flags):
        self._preprocessor_flags = list_of_flags[:]

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
            grab_folder(self.config, src=self.lfric_core_root / dir, dst_label='')

        # Copy the PSyclone Config file into a separate directory
        dir = "etc"
        grab_folder(self.config, src=self.lfric_core_root / dir,
                    dst_label='psyclone_config')

    def find_source_files(self, path_filters=None):
        if path_filters is None:
            path_filters = []
        find_source_files(self.config,
                          path_filters=([Exclude('unit-test', '/test/')] +
                                        path_filters))

    def get_rose_meta(self):
        return ""

    def configurator(self):
        rose_meta = self.get_rose_meta()
        if rose_meta:
            # Ideally we would want to get all source files created in
            # the build directory, but then we need to know the list of
            # files to add them to the list of files to process
            configurator(self.config, lfric_core_source=self.lfric_core_root,
                         lfric_apps_source=self.lfric_apps_root,
                         gpl_utils_source=self.gpl_utils_source,
                         config_dir=self.config.source_root,
                         rose_meta_conf=rose_meta)

    def preprocess_c(self, path_flags=None):
        preprocess_c(self.config, common_flags=self._preprocessor_flags,
                     path_flags=path_flags)

    def preprocess_fortran(self, path_flags=None):
        preprocess_fortran(self.config, common_flags=self._preprocessor_flags,
                           path_flags=path_flags)

    def preprocess_x90(self):
        preprocess_x90(self.config, common_flags=self._preprocessor_flags)

    def get_transformation_script(self):
        return ""

    def get_psyclone_config(self):
        return ["--config", self._psyclone_config]

    def psyclone(self):
        psyclone(self.config, kernel_roots=[self.config.build_output],
                 transformation_script=self.get_transformation_script(),
                 cli_args=self.get_psyclone_config())

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
    from grab_lfric_utils import gpl_utils_source_config
    fab_base = FabBase(name="command-line-test",
                       gpl_utils_config=gpl_utils_source_config,
                       root_symbol=None)
