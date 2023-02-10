"""
Sparse Eigenvalue Solvers
-------------------------

The submodules of sparse.linalg._eigen:
    1. lobpcg: Locally Optimal Block Preconditioned Conjugate Gradient Method

"""
from scipy._lib._testutils import PytestTester

from . import arpack
from ._svds import svds
from .arpack import *
from .lobpcg import *

__all__ = ["ArpackError", "ArpackNoConvergence", "eigs", "eigsh", "lobpcg", "svds"]

test = PytestTester(__name__)
del PytestTester
