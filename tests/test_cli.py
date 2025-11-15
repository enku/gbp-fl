# pylint: disable=missing-docstring
from unittest import TestCase

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, given


@given(testkit.gbpcli)
class HandlerTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        cli = fixtures.gbpcli
        console = fixtures.console

        status = cli("gbp fl")

        self.assertEqual(status, 1)
        self.assertEqual(console.stdout, "$ gbp fl\n")
        self.assertTrue(console.stderr.startswith("Subcommands:"))
