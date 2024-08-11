#! /usr/bin/env python3

from fab.tools import Gcc, Gfortran, Icc, Ifort, ToolRepository

from default.config import Config as DefaultConfig


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


class Config(DefaultConfig):
    '''For NCI, add the Tau wrapper.
    '''

    def __init__(self):
        super().__init__()
        tr = ToolRepository()
        tr.set_default_compiler_suite("intel-classic")

        # A compiler will also be added automatically
        # as linker, i.e. linker-tau-gnu etc
        for tool in [TauGnuFortran, TauIntelFortran, TauGnuC, TauIntelC]:
            tr.add_tool(tool())
