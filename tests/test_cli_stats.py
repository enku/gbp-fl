"""tests for the fl stats subcommand"""

# pylint: disable=missing-docstring
from unittest import TestCase

from gbp_testkit import fixtures as testkit
from gentoo_build_publisher.cache import cache
from unittest_fixtures import Fixtures, fixture, given, where

from gbp_fl.types import STATS_CACHE_KEY, FileStats, MachineStats

from . import lib


@fixture()
def stats_fixture(_: Fixtures) -> FileStats:
    return FileStats(
        total=9605802 + 9540343,
        by_machine={
            "polaris": MachineStats(total=9605802, build_count=33),
            "lighthouse": MachineStats(total=9540343, build_count=35),
        },
    )


@fixture(stats_fixture)
def cached_stats(fixtures: Fixtures) -> None:
    cache.clear()
    cache.set(STATS_CACHE_KEY, fixtures.stats)


@given(cached_stats, lib.environ, testkit.gbpcli)
@where(environ={"GBPCLI_MYMACHINES": "lighthouse", "LC_NUMERIC": "en_US.utf8"})
class StatsTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        """Test basic functionality of the command"""
        status = fixtures.gbpcli("gbp fl stats")

        console = fixtures.console
        self.assertEqual(status, 0, console.stderr)

        expected = STATS_OUTPUT_ALL
        self.assertEqual(console.stdout, expected)

    def test_with_mine(self, fixtures: Fixtures) -> None:
        """Test with the --mine flag"""
        status = fixtures.gbpcli("gbp fl stats --mine")

        console = fixtures.console
        self.assertEqual(status, 0, console.stderr)

        expected = STATS_OUTPUT_MINE
        self.assertEqual(console.stdout, expected)


STATS_OUTPUT_ALL = """$ gbp fl stats
           19,146,145 Files           
╭────────────┬───────────┬───────────╮
│ Machine    │     Files │ Per Build │
├────────────┼───────────┼───────────┤
│ polaris    │ 9,605,802 │   291,084 │
│ lighthouse │ 9,540,343 │   272,581 │
╰────────────┴───────────┴───────────╯
"""
STATS_OUTPUT_MINE = """$ gbp fl stats --mine
           9,540,343 Files            
╭────────────┬───────────┬───────────╮
│ Machine    │     Files │ Per Build │
├────────────┼───────────┼───────────┤
│ lighthouse │ 9,540,343 │   272,581 │
╰────────────┴───────────┴───────────╯
"""
