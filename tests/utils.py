"""Test utilities"""

from tarfile import TarInfo

from gbp_fl.types import Build, BuildLike, Package

# pylint: disable=missing-docstring


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
