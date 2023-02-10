from scipy._lib._testutils import PytestTester

from ._gcrotmk import gcrotmk

# from info import __doc__
from .iterative import *
from .lgmres import lgmres
from .lsmr import lsmr
from .lsqr import lsqr
from .minres import minres
from .tfqmr import tfqmr

"Iterative Solvers for Sparse Linear Systems"


__all__ = [
    "bicg",
    "bicgstab",
    "cg",
    "cgs",
    "gcrotmk",
    "gmres",
    "lgmres",
    "lsmr",
    "lsqr",
    "minres",
    "qmr",
    "tfqmr",
]

test = PytestTester(__name__)
del PytestTester
