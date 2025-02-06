"""Test utilities"""

import datetime as dt
import os
from contextlib import contextmanager
from tarfile import TarInfo
from typing import Any, Generator

from django.test.client import Client

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


def graphql(query: str, variables: dict[str, Any] | None = None) -> Any:
    """Execute GraphQL query on the Django test client.

    Return the parsed JSON response
    """
    client = Client()
    response = client.post(
        "/graphql",
        {"query": query, "variables": variables},
        content_type="application/json",
    )

    return response.json()


@contextmanager
def cd(path: str) -> Generator[None, None, None]:
    cwd = os.getcwd()

    os.chdir(path)
    yield
    os.chdir(cwd)
