"""tests for the fl stats subcommand"""

# pylint: disable=missing-docstring
from unittest import TestCase

from gbp_testkit import fixtures as testkit
from unittest_fixtures import Fixtures, given, where

from . import lib


@given(lib.cached_stats, lib.environ, testkit.gbpcli)
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
