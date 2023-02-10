# This module exists only to allow Sphinx to generate docs
# for the result objects returned by some functions in stats
# _without_ adding them to the main stats documentation page.

"""
Result classes
--------------

.. currentmodule:: scipy.stats._result_classes

.. autosummary::
   :toctree: generated/

   RelativeRiskResult
   BinomTestResult
   TukeyHSDResult
   PearsonRResult
   FitResult

"""
from ._binomtest import BinomTestResult
from ._fit import FitResult
from ._hypotests import TukeyHSDResult
from ._relative_risk import RelativeRiskResult
from ._stats_py import PearsonRResult

__all__ = [
    "BinomTestResult",
    "RelativeRiskResult",
    "TukeyHSDResult",
    "PearsonRResult",
    "FitResult",
]
