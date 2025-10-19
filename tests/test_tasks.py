"""Tests for gbp-fl async tasks"""

# The tasks, by design, do basically nothing. We just have to assert the call the
# appropriate functions with the appropriate args

from unittest import TestCase, mock

from unittest_fixtures import Fixtures, given

from gbp_fl.gateway import gateway
from gbp_fl.worker import tasks

from . import lib

# pylint: disable=missing-docstring


@given(lib.build)
class IndexBuildTests(TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.package_utils")
    def test(
        self, package_utils: mock.Mock, set_process: mock.Mock, fixtures: Fixtures
    ) -> None:
        build = fixtures.build
        tasks.index_build(build.machine, build.build_id)

        package_utils.index_build(build)

        set_process.assert_called_once_with(build, "index")

    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    def test_caches_stats(self, _: mock.Mock, fixtures: Fixtures) -> None:
        build = fixtures.build

        gateway.cache.delete("stats")
        tasks.index_build(build.machine, build.build_id)

        self.assertTrue(gateway.cache.contains("stats"))


@given(lib.build)
class DeindexBuildTests(TestCase):
    @mock.patch("gbp_fl.gateway.GBPGateway.set_process")
    @mock.patch("gbp_fl.records.Repo.from_settings")
    def test(
        self, repo_from_settings: mock.Mock, set_process: mock.Mock, fixtures: Fixtures
    ) -> None:
        build = fixtures.build
        tasks.deindex_build(build.machine, build.build_id)

        repo = repo_from_settings.return_value
        repo.files.deindex_build.assert_called_once_with(build.machine, build.build_id)

        set_process.assert_called_once_with(build, "deindex")

    def test_caches_stats(self, fixtures: Fixtures) -> None:
        build = fixtures.build

        gateway.cache.delete("stats")
        tasks.deindex_build(build.machine, build.build_id)

        self.assertTrue(gateway.cache.contains("stats"))
