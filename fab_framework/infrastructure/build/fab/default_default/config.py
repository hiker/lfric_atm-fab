#! /usr/bin/env python3

from fab.tools import Category, Gcc, Gfortran, Icc, Ifort, ToolRepository


class Mpif90Gnu(Gfortran):
    def __init__(self):
        super().__init__(name="mpif90-gnu",
                         exec_name="mpif90")


class Mpif90Intel(Ifort):
    def __init__(self):
        super().__init__(name="mpif90-intel",
                         exec_name="mpif90")


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
        # as linker, i.e. linker-mpif90-gnu etc
        for tool in [Mpif90Gnu, Mpif90Intel, TauGnuFortran, TauIntelFortran,
                     TauGnuC, TauIntelC]:
            tr.add_tool(tool)

    def update_toolbox(self, toolbox):
        '''This could be used to define different compiler flags etc.
        For now do nothing.'''
        # TODO: not sure if a site-specific script should actually ever
        # update the toolbox - the toolbox is mostly defined based on
        # command line parameters, and should not be modified.
        # For now leave it here, and once we have fixed the support
        # for compiler flags (with modes etc), this can be refactored.
        pass
