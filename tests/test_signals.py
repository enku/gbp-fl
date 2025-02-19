# pylint: disable=missing-docstring
import logging
import shutil
from pathlib import Path
from unittest import mock

import unittest_fixtures as uf
from django.test import TestCase

from gbp_fl import gateway
from gbp_fl.records import Repo
from gbp_fl.types import Build

TESTDIR = Path(__file__).parent

logging.basicConfig(handlers=[logging.NullHandler()])


@uf.requires("publisher")
class GBPTestCase(uf.TestCase, TestCase):
    options = {"records_backend": "django"}


@uf.depends("gbp_package", build_record="record")
def binpkg(_o: uf.FixtureOptions, f: uf.Fixtures) -> Path:
    gbp = gateway.GBPGateway()
    path = Path(gbp.get_full_package_path(f.build_record, f.gbp_package))
    path.parent.mkdir(parents=True)
    shutil.copy(TESTDIR / "assets/sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar", path)

    with open(path.parents[2] / "Packages", "w", encoding="utf8") as meta:
        meta.write(PACKAGES)

    return path


@uf.requires("worker", "gbp_package", "settings", binpkg)
class PostPulledTests(GBPTestCase):
    def test(self) -> None:
        f = self.fixtures
        repo: Repo = Repo.from_settings(f.settings)
        gbp = gateway.GBPGateway()
        _ = None

        with mock.patch("gbp_fl.package_utils.Repo.from_settings", return_value=repo):
            gbp.emit_signal(
                "postpull", build=f.build_record, packages=_, gbp_metadata=_
            )

        content_files = list(
            repo.files.for_package(
                f.build_record.machine,
                f.build_record.build_id,
                f"{f.gbp_package.cpv}-{f.gbp_package.build_id}",
            )
        )
        self.assertEqual(len(content_files), 10)

    def test_with_empty_tar(self) -> None:
        f = self.fixtures
        repo: Repo = Repo.from_settings(f.settings)
        gbp = gateway.GBPGateway()
        _ = None

        shutil.copy(TESTDIR / "assets/empty.tar", f.binpkg)

        with mock.patch("gbp_fl.package_utils.Repo.from_settings", return_value=repo):
            gbp.emit_signal(
                "postpull", build=f.build_record, packages=_, gbp_metadata=_
            )

        content_files = list(
            repo.files.for_package(
                f.build_record.machine, f.build_record.build_id, f.gbp_package.cpv
            )
        )
        self.assertEqual(len(content_files), 0)

    def test_pull_with_no_package_manifest(self) -> None:
        f = self.fixtures
        repo: Repo = Repo.from_settings(f.settings)
        gbp = gateway.GBPGateway()
        _ = None

        package_manifest: Path = f.binpkg.parents[2] / "Packages"
        package_manifest.unlink()

        with mock.patch("gbp_fl.package_utils.Repo.from_settings", return_value=repo):
            gbp.emit_signal(
                "postpull", build=f.build_record, packages=_, gbp_metadata=_
            )

        content_files = list(
            repo.files.for_package(
                f.build_record.machine,
                f.build_record.build_id,
                f"{f.gbp_package.cpv}-{f.gbp_package.build_id}",
            )
        )
        self.assertEqual(len(content_files), 0)


@uf.requires("worker", "settings", "bulk_content_files")
class PostDeleteTests(GBPTestCase):
    def test(self) -> None:
        f = self.fixtures
        repo: Repo = Repo.from_settings(f.settings)
        repo.files.bulk_save(f.bulk_content_files)
        gbp = gateway.GBPGateway()

        self.assertEqual(repo.files.count(None, None, None), 6)

        with mock.patch("gbp_fl.package_utils.Repo.from_settings", return_value=repo):
            build = Build(machine="polaris", build_id="26")
            gbp.emit_signal("postdelete", build=build)

        self.assertEqual(repo.files.count(None, None, None), 3)


@uf.requires("gbp_package", binpkg, build_record="record")
class GetPackageContentsTests(GBPTestCase):
    def test(self) -> None:
        f = self.fixtures
        gbp = gateway.GBPGateway()

        contents = gbp.get_package_contents(f.build_record, f.gbp_package)

        self.assertEqual(len(list(contents)), 19)


PACKAGES = """\
ACCEPT_KEYWORDS: amd64 ~amd64
ACCEPT_LICENSE: @FREE
ACCEPT_PROPERTIES: *
ACCEPT_RESTRICT: *
ARCH: amd64
CBUILD: x86_64-pc-linux-gnu
CHOST: x86_64-pc-linux-gnu
ELIBC: glibc
GENTOO_MIRRORS: http://distfiles.gentoo.org
INSTALL_MASK: /usr/share/doc
KERNEL: linux
PACKAGES: 1
TIMESTAMP: 1738033770
VERSION: 0

BUILD_ID: 1
BUILD_TIME: 1725728729
CPV: sys-libs/mtdev-1.1.7
DEFINED_PHASES: configure install
DEPEND: >=sys-kernel/linux-headers-2.6.31
EAPI: 8
KEYWORDS: ~alpha amd64 arm arm64 ~hppa ~ia64 ~loong ~m68k ~mips ppc ppc64 ~riscv ~s390 sparc x86
LICENSE: MIT
MD5: 5c9f95bf9b86a05e7348e14b64badd69
PATH: sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar
PROVIDES: x86_64: libmtdev.so.1
RDEPEND: >=sys-libs/glibc-2.40
REQUIRES: x86_64: libc.so.6
SHA1: 837d681085179a949527938c71f5f32d8fd8ffc9
SIZE: 40960
USE: abi_x86_64 amd64 elibc_glibc kernel_linux
MTIME: 1725728730
REPO: gentoo
"""
