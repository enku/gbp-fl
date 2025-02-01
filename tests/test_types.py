"""Tests for gbp_fl.types"""

# pylint: disable=missing-docstring
from unittest_fixtures import TestCase, requires

from gbp_fl.types import BinPkg, Build


@requires("now")
class BinPkgTests(TestCase):
    def test_cpv(self) -> None:
        fixtures = self.fixtures
        build = Build(machine="lighthouse", build_id="32267")
        binpkg = BinPkg(
            build=build,
            cpvb="x11-apps/xhost-1.0.10-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        self.assertEqual(binpkg.cpv, "x11-apps/xhost-1.0.10")

    def test_build_id(self) -> None:
        fixtures = self.fixtures
        build = Build(machine="lighthouse", build_id="32267")
        binpkg = BinPkg(
            build=build,
            cpvb="x11-apps/xhost-1.0.10-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        self.assertEqual(binpkg.build_id, 3)
