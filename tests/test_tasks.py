"""Tests for gbp-fl async tasks"""

# The tasks, by design, do basically nothing. We just have to assert the call the
# appropriate functions with the appropriate args

from unittest import TestCase, mock

from gbp_fl.types import Build
from gbp_fl.worker import tasks

# pylint: disable=missing-docstring


class IndexBuildTests(TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.package_utils")
    def test(self, package_utils: mock.Mock, set_process: mock.Mock) -> None:
        tasks.index_build("babette", "1505")
        build = Build(machine="babette", build_id="1505")

        package_utils.index_build(build)

        set_process.assert_called_once_with(build, "index")


class DeindexBuildTests(TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.records.Repo.from_settings")
    def test(self, repo_from_settings: mock.Mock, set_process: mock.Mock) -> None:
        tasks.deindex_build("babette", "1505")
        build = Build(machine="babette", build_id="1505")

        repo = repo_from_settings.return_value
        repo.files.deindex_build.assert_called_once_with("babette", "1505")

        set_process.assert_called_once_with(build, "deindex")
