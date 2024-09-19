#!/usr/bin/env python3

'''This file contains a function that sets the default flags for all
GNU based compilers in the ToolRepository.

This function gets called from the default site-specific config file
'''

from fab.build_config import BuildConfig
from fab.tools import Category, ToolRepository


def setup_gnu(build_config: BuildConfig):
    '''Defines the default flags for all GNU compilers.

    :para build_config: the build config from which required parameters
        can be taken.
    '''

    tr = ToolRepository()
    gfortran = tr.get_tool(Category.FORTRAN_COMPILER, "gfortran")
    flags = ['-ffree-line-length-none', '-g',
             '-Werror=character-truncation', '-Werror=unused-value',
             '-Werror=tabs', '-fdefault-real-8', '-fdefault-double-8',
             '-Ditworks'
             ]
    gfortran.add_flags(flags)

    gfortran = tr.get_tool(Category.LINKER, "linker-gfortran")
    gfortran.add_lib_flags("netcdf", ["$(nf-config --flibs)",
                                      "$(nc-config --libs)"],
                           silent_replace=True)
    gfortran.add_lib_flags("yaxt", ["-lyaxt", "-lyaxt_c"])
    gfortran.add_lib_flags("xios", ["-lxios"])
    gfortran.add_lib_flags("hdf5", ["-lhdf5"])
    gfortran.add_lib_flags("stdc++", ["-lstdc++"])

    gfortran = tr.get_tool(Category.LINKER, "linker-mpif90-gfortran")
    gfortran.add_lib_flags("netcdf", ["$(nf-config --flibs)",
                                      "$(nc-config --libs)"],
                           silent_replace=True)
    gfortran.add_lib_flags("yaxt", ["-lyaxt", "-lyaxt_c"])
    gfortran.add_lib_flags("xios", ["-lxios"])
    gfortran.add_lib_flags("hdf5", ["-lhdf5"])
    gfortran.add_lib_flags("stdc++", ["-lstdc++"])
