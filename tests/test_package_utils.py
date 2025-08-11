"""Tests for the package_utils module"""

from pathlib import Path
from unittest import TestCase, mock

import gbp_testkit.fixtures as testkit
from django.test import TestCase as DjangoTestCase
from unittest_fixtures import Fixtures, given, where

from gbp_fl import package_utils
from gbp_fl.records import files_backend
from gbp_fl.types import ContentFileInfo

from . import lib

# pylint: disable=missing-docstring,unused-argument

MOCK_PREFIX = "gbp_fl.package_utils."


@given(lib.bulk_packages, lib.gateway, lib.tarinfo, lib.build)
@where(
    bulk_packages="""
    app-crypt/rhash-1.4.5
    dev-libs/libgcrypt-1.11.0-r2
    dev-libs/openssl-3.3.2-r2
    dev-libs/wayland-protocols-1.39
    net-dns/c-ares-1.34.4
"""
)
@where(build__machine="babette", build__build_id="1505")
class IndexBuildTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        mock_gw = fixtures.gateway
        package = fixtures.bulk_packages[0]
        build = fixtures.build
        mock_gw.packages[build] = [package]
        mock_gw.contents[build, package] = [fixtures.tarinfo]
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}gateway", new=mock_gw):
            with mock.patch(f"{MOCK_PREFIX}repo", new=repo):
                package_utils.index_build(build)

        self.assertEqual(repo.files.count(None, None, None), 1)

        content_file = next(iter(repo.files.files.values()))
        self.assertEqual(content_file.path, Path("/bin/bash"))
        self.assertEqual(content_file.size, 22)

    def test_when_no_package(self, fixtures: Fixtures) -> None:
        mock_gw = fixtures.gateway
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}gateway", new=mock_gw):
            with mock.patch(f"{MOCK_PREFIX}repo", new=repo):
                package_utils.index_build(fixtures.build)

        self.assertEqual(repo.files.count(None, None, None), 0)


# Any test that uses "record" depends on Django, because "records" depends on Django.
# This needs to be fixed
@where(records_db__backend="django")
@given(lib.gbp_package, testkit.record)
class MakeContentFileTests(DjangoTestCase):
    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        info = ContentFileInfo(name="/bin/bash", mtime=1738258812, size=8829)

        result = package_utils.make_content_file(f.record, f.gbp_package, info)

        self.assertEqual(result.path, Path("/bin/bash"))
        self.assertEqual(result.size, 8829)
