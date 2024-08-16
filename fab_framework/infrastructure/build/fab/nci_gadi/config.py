#! /usr/bin/env python3

'''This module contains the default configuration for NCI. It will be invoked
by the Baf scripts. This script:
- sets intel-classic as the default compiler suite to use.
- Adds the tau compiler wrapper as (optional) compilers to the ToolRepository.

'''


from fab.tools import (Category, Compiler, CompilerWrapper, ToolRepository)

from default.config import Config as DefaultConfig


class Tauf90(CompilerWrapper):
    '''Class for the Tau profiling Fortran compiler wrapper.
    It will be using the name "tau-COMPILER_NAME", but will call tau_f90.sh.

    :param compiler: the compiler that the tau_f90.sh wrapper will use.
    '''

    def __init__(self, compiler: Compiler):
        super().__init__(name=f"tau-{compiler.name}",
                         exec_name="tau_f90.sh", compiler=compiler, mpi=True)


class Taucc(CompilerWrapper):
    '''Class for the Tau profiling C compiler wrapper.
    It will be using the name "tau-COMPILER_NAME", but will call tau_cc.sh.

    :param compiler: the compiler that the tau_cc.sh wrapper will use.
    '''

    def __init__(self, compiler: Compiler):
        super().__init__(name=f"tau-{compiler.name}",
                         exec_name="tau_cc.sh", compiler=compiler, mpi=True)


class Config(DefaultConfig):
    '''For NCI, make intel the default, and add the Tau wrapper.
    '''

    def __init__(self):
        super().__init__()
        tr = ToolRepository()
        tr.set_default_compiler_suite("intel-classic")

        # Add the tau wrappers for Fortran and C. Note that add_tool
        # will automatically add them as a linker as well.
        for ftn in ["ifort", "gfortran"]:
            compiler = tr.get_tool(Category.FORTRAN_COMPILER, ftn)
            tr.add_tool(Tauf90(compiler))

        for cc in ["icc", "gcc"]:
            compiler = tr.get_tool(Category.C_COMPILER, cc)
            tr.add_tool(Taucc(compiler))
