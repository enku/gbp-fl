"""Utilities for gbp-fl"""

import re
from dataclasses import dataclass
from tarfile import TarFile

from gbp_fl.types import MissingPackageIdentifier, Package

PKGSPEC_RE_STR = r"""
(?P<p>[a-z].*)-
(?P<v>[0-9].*)-
(?P<b>[0-9]*)
"""

PKGSPEC_RE = re.compile(PKGSPEC_RE_STR, re.I | re.X)


@dataclass
class Parsed:
    """Parsed package spec"""

    machine: str
    build_id: str
    c: str
    p: str
    v: str
    b: int

    @property
    def cpvb(self) -> str:
        """The cpvb (category, version, package, build_id) for the package"""
        return f"{self.c}/{self.p}-{self.v}-{self.b}"


def parse_pkgspec(pkgspec: str) -> Parsed | None:
    """Parse the given spec"""
    parts = pkgspec.split("/")

    if len(parts) != 4:
        return None

    machine, build_id, c, pvb = parts

    if match := PKGSPEC_RE.match(pvb):
        p, v, b = match.groups()
        parsed = Parsed(machine=machine, build_id=build_id, c=c, p=p, v=v, b=int(b))
        return parsed
    return None


def ensure_package_identifier(package: Package, tarfile: TarFile) -> None:
    """Raise MissingPackageIdentifier if tarfile is missing the required identifier"""
    pv = package.cpv.partition("/")[2]
    package_identifier = f"{pv}-{package.build_id}/gpkg-1"

    if package_identifier in tarfile.getnames():
        return

    msg = f"Expected {package_identifier} in the archive, but it was not found."
    raise MissingPackageIdentifier(msg)
