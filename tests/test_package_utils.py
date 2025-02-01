"""Tests for the package_utils module"""

from pathlib import Path
from unittest import mock

import unittest_fixtures as uf

from gbp_fl import package_utils
from gbp_fl.records import files_backend
from gbp_fl.types import Build, ContentFileInfo

from .utils import MockGBPGateway

# pylint: disable=missing-docstring

MOCK_PREFIX = "gbp_fl.package_utils."


@uf.requires("bulk_packages")
class IndexPackagesTests(uf.TestCase):
    options = {
        "bulk_packages": """
            app-crypt/rhash-1.4.5
            dev-libs/libgcrypt-1.11.0-r2
            dev-libs/openssl-3.3.2-r2
            dev-libs/wayland-protocols-1.39
            net-dns/c-ares-1.34.4
        """
    }

    def test(self) -> None:
        mock_gw = MockGBPGateway()
        build = Build(machine="babette", build_id="1505")
        package = self.fixtures.bulk_packages[0]
        mock_gw.packages[build] = [package]
        mock_tarinfo = mock.Mock(mtime=0, size=22)
        mock_tarinfo.isdir.return_value = False
        mock_tarinfo.name = "image/bin/bash"
        mock_gw.contents[build, package] = [mock_tarinfo]
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}GBPGateway", return_value=mock_gw):
            with mock.patch(f"{MOCK_PREFIX}Repo.from_settings", return_value=repo):
                package_utils.index_packages(build)

        self.assertEqual(repo.files.count(None, None, None), 1)

        content_file = next(iter(repo.files.files.values()))
        self.assertEqual(content_file.path, Path("/bin/bash"))
        self.assertEqual(content_file.size, 22)

    def test_when_no_package(self) -> None:
        mock_gw = MockGBPGateway()
        build = Build(machine="babette", build_id="1505")
        repo = mock.Mock(files=files_backend("memory"))

        with mock.patch(f"{MOCK_PREFIX}GBPGateway", return_value=mock_gw):
            with mock.patch(f"{MOCK_PREFIX}Repo.from_settings", return_value=repo):
                package_utils.index_packages(build)

        self.assertEqual(repo.files.count(None, None, None), 0)


@uf.requires("build_record", "gbp_package")
class MakeContentFileTests(uf.TestCase):
    def test(self) -> None:
        f = self.fixtures
        info = ContentFileInfo(name="/bin/bash", mtime=1738258812, size=8829)

        result = package_utils.make_content_file(f.build_record, f.gbp_package, info)

        self.assertEqual(result.path, Path("/bin/bash"))
        self.assertEqual(result.size, 8829)
