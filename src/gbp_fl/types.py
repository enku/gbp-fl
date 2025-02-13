"""gbp-fl data types

Builds contain BinPkgs and BinPkgs contain ContentFiles, which have Paths and other
metadata.
"""

import datetime as dt
from dataclasses import dataclass
from pathlib import PurePath as Path
from typing import Protocol


@dataclass(frozen=True)
class Package:
    """GBP Package proxy object"""

    cpv: str
    repo: str
    build_id: int
    build_time: int
    path: str


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

    @property
    def cpv(self) -> str:
        """The BinPkg's cpv"""
        return self.cpvb.rsplit("-", 1)[0]

    @property
    def build_id(self) -> int:
        """The BinPkg's build id"""
        return int(self.cpvb.rsplit("-", 1)[1])


@dataclass(frozen=True, kw_only=True, slots=True)
class ContentFile:
    """A file in a BinPkg (in a Build)"""

    binpkg: BinPkg
    path: Path
    timestamp: dt.datetime

    size: int
    """size of file in bytes"""


class BuildLike(Protocol):  # pylint: disable=too-few-public-methods
    """A GBP Build that we want to pretend we don't know is a gbp-fl Build"""

    machine: str
    build_id: str


@dataclass(frozen=True)
class ContentFileInfo:
    """Interface for ContentFile metadata

    IRL this wrapper around the tarfile.TarInfo object
    """

    # pylint: disable=too-few-public-methods, missing-docstring
    name: str
    """name of the image file"""

    mtime: int
    """modification time in seconds since epoch"""

    size: int
    """file size in bytes"""


class MissingPackageIdentifier(LookupError):
    """Raised when tar archive is missing GLEP-78 package identifier"""
