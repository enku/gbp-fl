"""tests for gbp-fl templatetags"""

# pylint: disable=missing-docstring,unused-argument

from unittest import TestCase

import gbp_testkit.fixtures as testkit
from django.core.cache import cache
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, where

from gbp_fl.django.gbp_fl.templatetags.gbp_fl import file_count

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
