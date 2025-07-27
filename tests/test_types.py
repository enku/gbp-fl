"""Tests for gbp_fl.types"""

# pylint: disable=missing-docstring
from unittest import TestCase

from unittest_fixtures import Fixtures, given

from gbp_fl.types import BinPkg, Build, Package

from . import lib


@given(lib.now)
class BinPkgTests(TestCase):
    def test_cpv(self, fixtures: Fixtures) -> None:
        build = Build(machine="lighthouse", build_id="32267")
        binpkg = BinPkg(
            build=build,
            cpvb="x11-apps/xhost-1.0.10-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        self.assertEqual(binpkg.cpv, "x11-apps/xhost-1.0.10")

    def test_build_id(self, fixtures: Fixtures) -> None:
        build = Build(machine="lighthouse", build_id="32267")
        binpkg = BinPkg(
            build=build,
            cpvb="x11-apps/xhost-1.0.10-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        self.assertEqual(binpkg.build_id, 3)


class PackageTests(TestCase):
    def test_cpvb(self) -> None:
        p = Package(
            cpv="x11-apps/xhost-1.0.10",
            build_id=3,
            repo="gentoo",
            build_time=0,
            path="x11-apps/xhost/xhost-1.0.10-3.gpkg.tar",
        )

        self.assertEqual("x11-apps/xhost-1.0.10-3", p.cpvb)
