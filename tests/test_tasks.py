"""Tests for gbp-fl async tasks"""

# The tasks, by design, do basically nothing. We just have to assert the call the
# appropriate functions with the appropriate args

from unittest import mock

import unittest_fixtures as uf

from gbp_fl.types import Build
from gbp_fl.worker import tasks

# pylint: disable=missing-docstring


class IndexPackagesTests(uf.TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.package_utils")
    def test(self, package_utils: mock.Mock, set_process: mock.Mock) -> None:
        tasks.index_packages("babette", "1505")
        build = Build(machine="babette", build_id="1505")

        package_utils.index_packages.assert_called_once_with(build)

        expected = [mock.call(build, "index"), mock.call(build, "clean")]
        set_process.assert_has_calls(expected)


class DeleteFromBuildTests(uf.TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.records.Repo.from_settings")
    def test(self, repo_from_settings: mock.Mock, set_process: mock.Mock) -> None:
        tasks.delete_from_build("babette", "1505")
        build = Build(machine="babette", build_id="1505")

        repo = repo_from_settings.return_value
        repo.files.delete_from_build.assert_called_once_with("babette", "1505")

        expected = [mock.call(build, "deindex"), mock.call(build, "clean")]
        set_process.assert_has_calls(expected)
