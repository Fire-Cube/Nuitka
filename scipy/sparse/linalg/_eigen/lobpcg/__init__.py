"""
Locally Optimal Block Preconditioned Conjugate Gradient Method (LOBPCG)

LOBPCG is a preconditioned eigensolver for large symmetric positive definite
(SPD) generalized eigenproblems.

Call the function lobpcg - see help for lobpcg.lobpcg.

"""
from scipy._lib._testutils import PytestTester

from .lobpcg import *

__all__ = [s for s in dir() if not s.startswith("_")]

test = PytestTester(__name__)
del PytestTester
