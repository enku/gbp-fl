"""Test utilities"""

import argparse
import datetime as dt
import os
import shlex
from contextlib import contextmanager
from tarfile import TarInfo
from typing import Generator

import gbpcli
from gbpcli.config import Config
from gbpcli.types import Console

from gbp_fl.types import Build, BuildLike, Package

# pylint: disable=missing-docstring

LOCAL_TIMEZONE = dt.timezone(dt.timedelta(days=-1, seconds=61200), "PDT")


class MockGBPGateway:
    """Not a real gateway"""

    def __init__(self) -> None:
        self.builds: list[BuildLike] = []
        self.packages: dict[Build, list[Package]] = {}
        self.contents: dict[tuple[Build, Package], list[TarInfo]] = {}
        self.machines: list[str] = []

    def get_packages(self, build: Build) -> list[Package]:
        try:
            return self.packages[build]
        except KeyError:
            raise LookupError(build) from None

    def get_package_contents(self, build: Build, package: Package) -> list[TarInfo]:
        try:
            return self.contents[build, package]
        except KeyError:
            raise LookupError(build, package) from None

    def list_machine_names(self) -> list[str]:
        return self.machines


@contextmanager
def cd(path: str) -> Generator[None, None, None]:
    cwd = os.getcwd()

    os.chdir(path)
    yield
    os.chdir(cwd)


def parse_args(cmdline: str) -> argparse.Namespace:
    """Return cmdline as parsed arguments"""
    args = shlex.split(cmdline)
    parser = gbpcli.build_parser(Config(url="http://gbp.invalid/"))

    return parser.parse_args(args[1:])


def print_command(cmdline: str, console: Console) -> None:
    """Pretty print the cmdline to console"""
    console.out.print(f"[green]$ [/green]{cmdline}")
