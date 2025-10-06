"""gbp-fl's command-line interface

The gbpcli handler does nothing but print usage as `gbp fl` has subparsers itself and
there is nothing (yet) to do at the "root" level.
"""

import argparse
import functools
import importlib
from typing import IO, Any, Protocol

from gbpcli.gbp import GBP
from gbpcli.types import Console

HELP = "Access the Gentoo Build Publisher File List"
SUBCOMMANDS = ("fetch", "ls", "search", "stats")


# subpparsers' type appear to be undocumented/unpublished so we spec out as much as we
# need here.
class SubParsersProtocol(Protocol):
    # pylint: disable=missing-docstring,too-few-public-methods
    def add_parser(self, name: str, **kwargs: Any) -> argparse.ArgumentParser: ...


def handler(args: argparse.Namespace, _gbp: GBP, console: Console) -> int:
    """GBP File List"""
    print_usage(console.err.file)
    return 1


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Create parsers for subcommands"""
    subparsers = parser.add_subparsers()

    for subcommand in SUBCOMMANDS:
        add_subparser(subcommand, subparsers)


def add_subparser(name: str, subparsers: SubParsersProtocol) -> argparse.ArgumentParser:
    """Create a subparser for the given subcommand"""
    module = importlib.import_module(f"gbp_fl.cli.{name}")
    subparser = subparsers.add_parser(name, help=module.HELP)
    module.parse_args(subparser)
    subparser.set_defaults(func=getattr(module, "handler"))

    return subparser


def print_usage(io: IO[str]) -> None:
    """Print the usage to the given file handle"""
    uprint = functools.partial(print, file=io)
    uprint("Subcommands:")

    for subcommand in SUBCOMMANDS:
        uprint(f"  {subcommand}")
