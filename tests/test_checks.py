"""Test for gbp-fl checks"""

# pylint: disable=missing-docstring

from unittest import TestCase

from gbp_testkit import fixtures as testkit
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, where

from gbp_fl import checks

from . import lib


@given(testkit.publisher, lib.bulk_content_files, build1=lib.build, build2=lib.build)
@given(lib.repo, testkit.console, set_process=testkit.patch)
@where(build1__build="polaris.26")
@where(build2__build="polaris.27")
@where(set_process__target="gbp_ps.signals.set_process")
class AllIndicesHaveBuildsTests(TestCase):
    def test_good(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        publisher.pull(GBPBuild(machine="polaris", build_id="27"))

        status = checks.all_indices_have_builds(fixtures.console)

        self.assertEqual(status, (0, 0))

    def test_bad(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        console = fixtures.console

        status = checks.all_indices_have_builds(console)

        self.assertEqual(status, (0, 1))
        self.assertEqual(
            console.stderr,
            "Warning: an index exists for build polaris.27 that does not exist.\n",
        )


@given(testkit.publisher, lib.bulk_content_files, build1=lib.build, build2=lib.build)
@given(lib.repo, testkit.console, set_process=testkit.patch)
@where(build1__build="polaris.26")
@where(build2__build="polaris.27")
@where(set_process__target="gbp_ps.signals.set_process")
class AllBuildsHaveIndicesTests(TestCase):
    def test_good(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        publisher.pull(GBPBuild(machine="polaris", build_id="27"))

        status = checks.all_builds_have_indices(fixtures.console)

        self.assertEqual(status, (0, 0))

    def test_bad(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        publisher.pull(GBPBuild(machine="polaris", build_id="27"))
        repo.files.deindex_build("polaris", "27")
        console = fixtures.console

        status = checks.all_builds_have_indices(console)

        self.assertEqual(status, (0, 1))
        self.assertEqual(console.stderr, "Warning: build polaris.27 is not indexed.\n")


@given(testkit.gbpcli, lib.repo, testkit.publisher)
class CLITests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        status = fixtures.gbpcli("gbp check")

        self.assertEqual(status, 0)
