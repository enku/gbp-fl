"""tests for gbp-fl templatetags"""

# pylint: disable=missing-docstring,unused-argument

from unittest import TestCase

import gbp_testkit.fixtures as testkit
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, params, where

from gbp_fl.gateway import gateway
from gbp_fl.types import FileStats, MachineStats

from . import lib

CONTENTS = """
    polaris 26 app-arch/tar-1.35-1       /bin/gtar
    polaris 26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris 26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris 27 app-shells/bash-5.2_p37-1 /bin/bash
"""


@params(cached=[False, True])
@given(testkit.publisher, lib.bulk_content_files, build1=lib.build, build2=lib.build)
@given(lib.repo, testkit.client)
@where(bulk_content_files=CONTENTS)
@where(build1__build="polaris.26")
@where(build2__build="polaris.27")
class MachineDetaiViewTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        repo.files.bulk_save(fixtures.bulk_content_files)
        publisher.pull(GBPBuild(machine="polaris", build_id="26"))
        publisher.pull(GBPBuild(machine="polaris", build_id="27"))

        if not fixtures.cached:
            gateway.cache.delete("stats")

        response = fixtures.client.get("/machines/polaris/")

        expected = 'Files <span class="badge badge-primary badge-pill">4</span>'
        self.assertIn(expected, response.text)

        expected = (
            'Files per build <span class="badge badge-primary badge-pill">2</span>'
        )
        self.assertIn(expected, response.text)


@given(cache_clear=lambda _: gateway.cache.delete("stats"))
@given(testkit.client)
class DashboardViewTests(TestCase):
    def test_files_metric(self, fixtures: Fixtures) -> None:
        stats = FileStats(
            total=6,
            by_machine={
                "polaris": MachineStats(total=4, build_count=4),
                "lighthouse": MachineStats(total=2, build_count=1),
            },
        )
        gateway.cache.set("stats", stats)

        response = fixtures.client.get("/")

        expected = """\
<div class="col-lg metric" align="center">
  <span class="number" title="" data-target="6">0</span><span class="suffix"></span>
  <h2 class="label">Files</h2>
</div>"""
        self.assertIn(expected, response.text)

    def test_files_chart(self, fixtures: Fixtures) -> None:
        stats = FileStats(
            total=6,
            by_machine={
                "polaris": MachineStats(total=4, build_count=4),
                "lighthouse": MachineStats(total=2, build_count=1),
            },
        )
        gateway.cache.set("stats", stats)

        response = fixtures.client.get("/")

        expected = (
            '<script id="machineFiles" type="application/json">{'
            '"polaris": {"total": 4, "build_count": 4, "per_build": 1}, '
            '"lighthouse": {"total": 2, "build_count": 1, "per_build": 2}'
            "}</script>"
        )
        self.assertIn(expected, response.text)
