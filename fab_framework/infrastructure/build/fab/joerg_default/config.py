#! /usr/bin/env python3

from fab.tools import Category, Gcc, Gfortran, Icc, Ifort, ToolRepository

from default.config import Config as DefaultConfig

class Config(DefaultConfig):

    def __init__(self):
        super().__init__()

    def setup_gnu(self, build_config):
        super().setup_gnu(build_config)
        gfortran = ToolRepository().get_tool(Category.FORTRAN_COMPILER,
                                             "gfortran")
        gfortran.add_flags(
            [
                # The lib directory contains mpi.mod
                '-I', ('/home/joerg/work/spack/var/spack/environments/'
                       'lfric-v0/.spack-env/view/lib'),
                # mod_wait.mod
                '-I', ('/home/joerg/work/spack/var/spack/environments/'
                       'lfric-v0/.spack-env/view/include'),
                '-DITSUPERWORKS'
            ])
