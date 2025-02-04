# pylint: disable=missing-docstring
import argparse
from unittest import mock

from unittest_fixtures import TestCase

from gbp_fl import cli

from .utils import string_console


class HandlerTests(TestCase):
    def test(self) -> None:
        args = argparse.Namespace()
        gbp = mock.Mock()
        console, out, err = string_console()

        status = cli.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertTrue(err.getvalue().startswith("Subcommands:"))


class ParseArgsTests(TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
