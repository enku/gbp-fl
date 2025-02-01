"""Utilities for working with Packages"""

import datetime as dt
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import PurePath as Path

from gbp_fl.gateway import GBPGateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile, ContentFileInfo, Package


def index_packages(build: Build) -> None:
    """Save the given Build's packages to the database"""
    gbp = GBPGateway()
    executor = ThreadPoolExecutor()

    try:
        packages = gbp.get_packages(build) or []
    except LookupError:
        return

    wait(executor.submit(index_package, package, build) for package in packages)


def index_package(package: Package, build: Build) -> None:
    """Save the files from the given build/package"""
    gbp = GBPGateway()
    package_contents = gbp.get_package_contents
    repo = Repo.from_settings(Settings.from_environ())

    content_files = (
        make_content_file(
            build,
            package,
            ContentFileInfo(name=item.name, mtime=int(item.mtime), size=item.size),
        )
        for item in package_contents(build, package)
        if not item.isdir() and item.name.startswith("image/")
    )
    repo.files.bulk_save(content_files)


def make_content_file(
    build: Build, gbp_package: Package, metadata: ContentFileInfo
) -> ContentFile:
    """Return a ContentFile given the parameters"""
    timestamp = dt.datetime.fromtimestamp(metadata.mtime, tz=dt.UTC)
    path = Path(metadata.name.removeprefix("image"))
    binpkg = BinPkg(
        build=Build(machine=build.machine, build_id=build.build_id),
        cpvb=f"{gbp_package.cpv}-{gbp_package.build_id}",
        repo=gbp_package.repo,
        build_time=dt.datetime.fromtimestamp(gbp_package.build_time, dt.UTC),
    )
    return ContentFile(
        path=path, binpkg=binpkg, size=metadata.size, timestamp=timestamp
    )
