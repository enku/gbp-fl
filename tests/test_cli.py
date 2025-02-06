# pylint: disable=missing-docstring
import argparse
from unittest import mock

from unittest_fixtures import TestCase, requires

from gbp_fl import cli


@requires("console")
class HandlerTests(TestCase):
    def test(self) -> None:
        args = argparse.Namespace()
        gbp = mock.Mock()
        console = self.fixtures.console

        status = cli.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(console.out.file.getvalue(), "")
        self.assertTrue(console.err.file.getvalue().startswith("Subcommands:"))


class ParseArgsTests(TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
