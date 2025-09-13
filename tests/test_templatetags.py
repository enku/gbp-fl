"""tests for gbp-fl templatetags"""

# pylint: disable=missing-docstring,unused-argument

from unittest import TestCase

from django.core.cache import cache
from unittest_fixtures import Fixtures, given

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
