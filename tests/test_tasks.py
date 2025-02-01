"""Tests for gbp-fl async tasks"""

# The tasks, by design, do basically nothing. We just have to assert the call the
# appropriate functions with the appropriate args

from unittest import mock

import unittest_fixtures as uf

from gbp_fl.types import Build
from gbp_fl.worker import tasks

# pylint: disable=missing-docstring


class IndexPackagesTests(uf.TestCase):
    @mock.patch("gbp_fl.package_utils")
    def test(self, package_utils: mock.Mock) -> None:
        tasks.index_packages("babette", "1505")

        package_utils.index_packages.assert_called_once_with(
            Build(machine="babette", build_id="1505")
        )


class DeleteFromBuildTests(uf.TestCase):
    @mock.patch("gbp_fl.records.Repo.from_settings")
    def test(self, repo_from_settings: mock.Mock) -> None:
        tasks.delete_from_build("babette", "1505")

        repo = repo_from_settings.return_value
        repo.files.delete_from_build.assert_called_once_with("babette", "1505")
