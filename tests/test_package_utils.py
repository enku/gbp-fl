"""Tests for the package_utils module"""

from pathlib import Path
from unittest import TestCase, mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, given, where

from gbp_fl import package_utils
from gbp_fl.records import files_backend
from gbp_fl.types import ContentFileInfo, Package

from . import lib

# pylint: disable=missing-docstring,unused-argument

MOCK_PREFIX = "gbp_fl.package_utils."


@given(lib.repo, lib.bulk_packages, lib.gateway, lib.tarinfo, lib.build)
@where(
    bulk_packages="""
    app-crypt/rhash-1.4.5
    dev-libs/libgcrypt-1.11.0-r2
    dev-libs/openssl-3.3.2-r2
    dev-libs/wayland-protocols-1.39
    net-dns/c-ares-1.34.4
"""
)
@where(build="babette.1505")
class IndexBuildTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        mock_gw = fixtures.gateway
        package = fixtures.bulk_packages[0]
        build = fixtures.build
        mock_gw.packages[build] = [package]
        mock_gw.contents[build, package] = [fixtures.tarinfo]
        repo = fixtures.repo

        with mock.patch(f"{MOCK_PREFIX}gateway", new=mock_gw):
            package_utils.index_build(build, repo)

        self.assertEqual(repo.files.count(None, None, None), 1)

        content_file = next(iter(repo.files.files.values()))
        self.assertEqual(content_file.path, Path("/bin/bash"))
        self.assertEqual(content_file.size, 22)

    def test_when_no_package(self, fixtures: Fixtures) -> None:
        mock_gw = fixtures.gateway
        repo = fixtures.repo

        with mock.patch(f"{MOCK_PREFIX}gateway", new=mock_gw):
            package_utils.index_build(fixtures.build, repo)

        self.assertEqual(repo.files.count(None, None, None), 0)

    def test_with_actual_package(self, fixtures: Fixtures) -> None:
        build = fixtures.build
        package = Package(
            "sys-libs/mtdev-1.1.7",
            repo="gentoo",
            build_id=1,
            build_time=123,
            path=str(lib.TESTDIR / "assets/sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar"),
        )
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}gateway.get_packages") as get_packages:
            get_packages.return_value = [package]
            package_utils.index_build(build, repo)

        files = {
            i.path.name for i in repo.files.for_build(build.machine, build.build_id)
        }
        expected = {
            "mtdev-test",
            "mtdev-mapping.h",
            "mtdev-plumbing.h",
            "mtdev.h",
            "libmtdev.so",
            "libmtdev.so.1",
            "libmtdev.so.1.0.0",
            "mtdev.pc",
            "ChangeLog",
            "README",
        }
        self.assertEqual(files, expected)

    def test_with_xpak_package(self, fixtures: Fixtures) -> None:
        build = fixtures.build
        package = Package(
            "app-eselect/eselect-pinentry",
            repo="gentoo",
            build_id=1,
            build_time=123,
            path=str(lib.TESTDIR / "assets/eselect-pinentry-0.7.2-1.xpak"),
        )
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}gateway.get_packages") as get_packages:
            get_packages.return_value = [package]
            package_utils.index_build(build, repo)

        files = {
            str(i.path) for i in repo.files.for_build(build.machine, build.build_id)
        }
        self.assertEqual(files, {"/usr/share/eselect/modules/pinentry.eselect"})


@given(lib.gbp_package, record=testkit.build_record)
class MakeContentFileTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        info = ContentFileInfo(name="/bin/bash", mtime=1738258812, size=8829)

        result = package_utils.make_content_file(f.record, f.gbp_package, info)

        self.assertEqual(result.path, Path("/bin/bash"))
        self.assertEqual(result.size, 8829)
