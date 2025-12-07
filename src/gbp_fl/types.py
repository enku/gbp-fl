"""gbp-fl data types

Builds contain BinPkgs and BinPkgs contain ContentFiles, which have Paths and other
metadata.
"""

import datetime as dt
from dataclasses import dataclass, field
from pathlib import PurePath as Path
from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from gbp_fl.records import ContentFiles


@dataclass(frozen=True)
class Package:
    """GBP Package proxy object"""

    cpv: str
    repo: str
    build_id: int
    build_time: int
    path: str
    cpvb: str = field(init=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cpvb", f"{self.cpv}-{self.build_id}")


@dataclass(frozen=True, kw_only=True, slots=True)
class Build:
    """A GBP Build"""

    machine: str
    build_id: str

    @property
    def id(self) -> str:
        """Return the Build's string id"""
        return f"{self.machine}.{self.build_id}"


@dataclass(frozen=True, kw_only=True, slots=True)
class BinPkg:
    """A (binary) package"""

    build: Build

    cpv: str
    """category-package-version"""

    build_id: int
    """The binpkg's build_id"""

    repo: str
    """Repository where the package was built from"""

    build_time: dt.datetime

    def cpvb(self) -> str:
        """The BinPkg's cpvb"""
        return f"{self.cpv}-{self.build_id}"


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


@dataclass(kw_only=True, frozen=True)
class MachineStats:
    """machine-specific gbp-fl stats

    This data structure includes:

        - total: the total number of files from all packages in all builds for the
          machine
        - build_count: the number of builds the machine has
        - per_build: the average number of files per build. In other words
          total // build_count
    """

    total: int = 0
    build_count: int = 0
    per_build: int = field(init=False)

    def __post_init__(self) -> None:
        if self.total > 0 and self.build_count == 0:
            raise ValueError("Cannot have files but no builds")

        per_build = 0 if self.build_count == 0 else self.total // self.build_count
        object.__setattr__(self, "per_build", per_build)


@dataclass(kw_only=True, frozen=True)
class FileStats:
    """gbp-fl aggregated stats"""

    total: int = 0
    by_machine: dict[str, MachineStats] = field(default_factory=dict)

    @classmethod
    def collect(cls, files: "ContentFiles", machines_info: dict[str, int]) -> Self:
        """Given the files repo,  and machine info return the FileStats

        `machines_info` is a dict of machine_name => build_count
        """
        by_machine = {
            machine: MachineStats(
                total=files.count(machine, None, None),
                build_count=machines_info[machine],
            )
            for machine in machines_info
        }
        return cls(
            total=sum(by_machine[machine].total for machine in machines_info),
            by_machine=by_machine,
        )


class MissingPackageIdentifier(LookupError):
    """Raised when tar archive is missing GLEP-78 package identifier"""
