"""gbp-fl data types

Builds contain BinPkgs and BinPkgs contain ContentFiles, which have Paths and other
metadata.
"""

import datetime as dt
from dataclasses import dataclass
from pathlib import PurePath as Path


@dataclass(frozen=True, kw_only=True, slots=True)
class Build:
    """A GBP Build"""

    machine: str
    build_id: str


@dataclass(frozen=True, kw_only=True, slots=True)
class BinPkg:
    """A (binary) package"""

    build: Build

    cpvb: str
    """category-package-version-build_id"""

    repo: str
    """Repository where the package was built from"""

    build_time: dt.datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class ContentFile:
    """A file in a BinPkg (in a Build)"""

    binpkg: BinPkg
    path: Path
    timestamp: dt.datetime

    size: int
    """size of file in bytes"""
