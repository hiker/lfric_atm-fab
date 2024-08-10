#! /usr/bin/env python3

from fab.tools import Category, Gcc, Gfortran, Icc, Ifort, ToolRepository


class TauGnuFortran(Gfortran):
    def __init__(self):
        super().__init__(name="tau-gnu-fortran",
                         exec_name="tau_f90.sh")


class TauIntelFortran(Ifort):
    def __init__(self):
        super().__init__(name="tau-intel-fortran",
                         exec_name="tau_f90.sh")


class TauGnuC(Gcc):
    def __init__(self):
        super().__init__(name="tau-gnu-c",
                         exec_name="tau_cc.sh")


class TauIntelC(Icc):
    def __init__(self):
        super().__init__(name="tau-intel-c",
                         exec_name="tau_cc.sh")


class Config:
    def __init__(self):
        tr = ToolRepository()
        # A compiler will also be added automatically
        # as linker, i.e. linker-tau-gnu etc
        for tool in [TauGnuFortran, TauIntelFortran, TauGnuC, TauIntelC]:
            tr.add_tool(tool())

    def setup_classic_intel(self, build_config):
        tr = ToolRepository()
        ifort = tr.get_tool(Category.FORTRAN_COMPILER, "ifort")
        ifort.add_flags([])

    def setup_gnu(self, build_config):
        tr = ToolRepository()
        gfortran = tr.get_tool(Category.FORTRAN_COMPILER, "gfortran")
        flags = ['-ffree-line-length-none', '-g',
                 '-Werror=character-truncation', '-Werror=unused-value',
                 '-Werror=tabs', '-fdefault-real-8', '-fdefault-double-8',
                 '-Ditworks'
                 ]
        gfortran.add_flags(flags)

    def update_toolbox(self, build_config):
        '''This could be used to define different compiler flags etc.
        For now do nothing.'''
        # TODO: not sure if a site-specific script should actually ever
        # update the toolbox - the toolbox is mostly defined based on
        # command line parameters, and should not be modified.
        # For now leave it here, and once we have fixed the support
        # for compiler flags (with modes etc), this can be refactored.
        self.setup_classic_intel(build_config)
        self.setup_gnu(build_config)
