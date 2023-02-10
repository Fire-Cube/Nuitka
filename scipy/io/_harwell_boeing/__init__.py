from scipy._lib._testutils import PytestTester

# Deprecated namespaces, to be removed in v2.0.0
from . import hb
from ._fortran_format_parser import (
    BadFortranFormat,
    ExpFormat,
    FortranFormatParser,
    IntFormat,
)
from .hb import (
    HBFile,
    HBInfo,
    HBMatrixType,
    MalformedHeader,
    hb_read,
    hb_write,
)

__all__ = [
    "MalformedHeader",
    "hb_read",
    "hb_write",
    "HBInfo",
    "HBFile",
    "HBMatrixType",
    "FortranFormatParser",
    "IntFormat",
    "ExpFormat",
    "BadFortranFormat",
    "hb",
]

test = PytestTester(__name__)
del PytestTester
