"""tests for gbp-fl templatetags"""

# pylint: disable=missing-docstring,unused-argument

from unittest import TestCase

import gbp_testkit.fixtures as testkit
from django.core.cache import cache
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, where

from gbp_fl.django.gbp_fl.templatetags.gbp_fl import file_count, gbp_fl_dashboard

from . import lib


@given(lib.repo, lib.bulk_content_files, cache_clear=lambda _: cache.clear())
class FileCountTest(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        content_files = fixtures.bulk_content_files
        repo = fixtures.repo
        repo.files.bulk_save(content_files)

        result = file_count()

        self.assertEqual(result, len(content_files))
        self.assertIn("file-count", cache)

    def test_hits_cache(self, fixtures: Fixtures) -> None:
        cache.set("file-count", 30_000)

        result = file_count()

        self.assertEqual(result, 30_000)


CONTENTS = """
    polaris 26 app-arch/tar-1.35-1       /bin/gtar
    polaris 26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris 26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris 27 app-shells/bash-5.2_p37-1 /bin/bash
"""


@given(testkit.publisher, lib.bulk_content_files, build1=lib.build, build2=lib.build)
@given(lib.repo, testkit.client)
@where(bulk_content_files=CONTENTS)
@where(build1__build="polaris.26")
@where(build2__build="polaris.27")
class MachineDetaiViewTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        publisher.pull(GBPBuild(machine="polaris", build_id="27"))
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)

        response = fixtures.client.get("/machines/polaris/")

        expected = 'Files <span class="badge badge-primary badge-pill">4</span>'
        self.assertIn(expected, response.text)

        expected = (
            'Files per build <span class="badge badge-primary badge-pill">2</span>'
        )
        self.assertIn(expected, response.text)


@given(saved=lambda f: f.repo.files.bulk_save(f.bulk_content_files))
@given(lib.bulk_content_files, lib.repo)
@given(cache_clear=lambda _: cache.clear())
class GBPFLDashboardTests(TestCase):
    def test_contains_file_by_machines(self, fixtures: Fixtures) -> None:
        result = gbp_fl_dashboard(["lighthouse", "polaris"])

        self.assertIn("files_by_machine", result)

    def test_items_contain_integers(self, fixtures: Fixtures) -> None:
        machines = ["lighthouse", "polaris"]

        result = gbp_fl_dashboard(machines)

        for machine in machines:
            self.assertIsInstance(result["files_by_machine"][machine], int)

    def test_empty(self, fixtures: Fixtures) -> None:
        result = gbp_fl_dashboard([])

        self.assertEqual(result, {"files_by_machine": {}})

    def test_same_machine(self, fixtures: Fixtures) -> None:
        result = gbp_fl_dashboard(["lighthouse", "lighthouse"])

        self.assertEqual(result, {"files_by_machine": {"lighthouse": 2}})

    def test_bogus_machine(self, fixtures: Fixtures) -> None:
        result = gbp_fl_dashboard(["lighthouse", "bogus"])

        self.assertEqual(result, {"files_by_machine": {"bogus": 0, "lighthouse": 2}})

    def test_cached_value(self, fixtures: Fixtures) -> None:
        hash_ = "b370de14e94142d4a108a79df6d0e265a0ba3fa2e10f57c4b3a892b74c9f84aa"
        key = f"gbp-fl-dashboard.{hash_}"
        cache.set(key, {"files_by_machine": {"lighthouse": 30000}})

        result = gbp_fl_dashboard(["lighthouse"])

        self.assertEqual(result, {"files_by_machine": {"lighthouse": 30000}})
