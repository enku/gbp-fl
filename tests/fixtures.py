"""unittest fixtures"""

# pylint: disable=missing-docstring

import datetime as dt
from pathlib import PurePath as Path
from typing import Any

from unittest_fixtures import FixtureOptions, Fixtures, depends

from gbp_fl.types import BinPkg, Build, ContentFile


@depends("binpkg", "now")
def content_file(options: FixtureOptions, fixtures: Fixtures) -> ContentFile:
    args = get_options(
        options.get("content_file", {}),
        binpkg=fixtures.binpkg,
        path=Path("/bin/bash"),
        timestamp=fixtures.now,
        size=870400,
    )
    return ContentFile(**args)


@depends("now")
def bulk_content_files(
    options: FixtureOptions, fixtures: Fixtures
) -> list[ContentFile]:
    content_files: list[ContentFile] = []
    cf_defs: str = options.get("bulk_content_files", DEFAULT_CONTENTS).strip()
    for cf_def in cf_defs.split("\n"):
        cf_def = cf_def.strip()

        if not cf_def:
            continue

        parts = cf_def.split()
        machine, build_id, cpvb, path = parts[:4]

        try:
            repo_ = parts[4]
        except IndexError:
            repo_ = "gentoo"

        bld = Build(machine=machine, build_id=build_id)
        pkg = BinPkg(build=bld, cpvb=cpvb, build_time=fixtures.now, repo=repo_)
        content_files.append(
            ContentFile(binpkg=pkg, path=Path(path), timestamp=fixtures.now, size=22)
        )

    return content_files


@depends("build", "now")
def binpkg(options: FixtureOptions, fixtures: Fixtures) -> BinPkg:
    args = get_options(
        options.get("package", {}),
        build=fixtures.build,
        cpvb="app-shells/bash-5.2_p37-3",
        build_time=fixtures.now,
        repo=options.get("repo", "gentoo"),
    )
    return BinPkg(**args)


@depends()
def build(options: FixtureOptions, _fixtures: Fixtures) -> Build:
    args = get_options(options.get("build", {}), machine="lighthouse", build_id="34")

    return Build(**args)


@depends()
def now(options: FixtureOptions, _fixtures: Fixtures) -> dt.datetime:
    time: dt.datetime = options.get(
        "now", dt.datetime(2025, 1, 26, 12, 57, 37, tzinfo=dt.UTC)
    )
    return time


def get_options(options: FixtureOptions, **defaults: Any) -> FixtureOptions:
    return {item: options.get(item, default) for item, default in defaults.items()}


DEFAULT_CONTENTS = """
    lighthouse 34 app-shells/bash-5.2_p37-1 /bin/bash
    lighthouse 34 app-shells/bash-5.2_p37-1 /etc/skel
    polaris    26 app-arch/tar-1.35-1       /bin/gtar
    polaris    26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris    26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris    27 app-shells/bash-5.2_p37-1 /bin/bash
"""
