# pylint: disable=missing-docstring,unused-argument
import argparse
from unittest import TestCase, mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, given

from gbp_fl import cli


@given(testkit.console)
class HandlerTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        args = argparse.Namespace()
        gbp = mock.Mock()
        console = fixtures.console

        status = cli.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(console.out.file.getvalue(), "")
        self.assertTrue(console.err.file.getvalue().startswith("Subcommands:"))


class ParseArgsTests(TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
