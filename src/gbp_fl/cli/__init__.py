"""gbp-fl's command-line interface

The gbpcli handler does nothing but print usage as `gbp fl` has subparsers itself and
there is nothing (yet) to do at the "root" level.
"""

import argparse
import functools
import importlib
from typing import IO

from gbpcli.gbp import GBP
from gbpcli.types import Console

HELP = "Access the Gentoo Build Publisher File List"
SUBCOMMANDS = ("search", "fetch")


def handler(args: argparse.Namespace, _gbp: GBP, console: Console) -> int:
    """GBP File List"""
    print_usage(console.err.file)
    return 1


handler.__doc__ = HELP


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Create parsers for subcommands"""
    subparsers = parser.add_subparsers()

    for subcommand in SUBCOMMANDS:

        module = importlib.import_module(f"gbp_fl.cli.{subcommand}")
        subparser = subparsers.add_parser(subcommand, help=module.HELP)
        module.parse_args(subparser)
        subparser.set_defaults(func=getattr(module, "handler"))


def print_usage(io: IO[str]) -> None:
    """Print the usage to the given file handle"""
    uprint = functools.partial(print, file=io)
    uprint("Subcommands:")

    for subcommand in SUBCOMMANDS:
        uprint(f"  {subcommand}")
