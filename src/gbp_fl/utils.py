"""Utilities for gbp-fl"""

import re
from dataclasses import dataclass

# lighthouse/32284/www-client/firefox-135.0-1
PKGSPEC_RE_STR = r"""
(?P<machine>[a-z]\w*)/
(?P<build_id>[0-9]+)/
(?P<c>[a-z0-9]+-[a-z0-9]+)/
(?P<p>[a-z].*)-(?P<v>[0-9].*)-(?P<b>[0-9]*)
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
    if match := PKGSPEC_RE.match(pkgspec):
        parsed = Parsed(**match.groupdict())  # type: ignore
        parsed.b = int(parsed.b)
        return parsed
    return None
