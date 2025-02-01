"""unittest fixtures"""

# pylint: disable=missing-docstring

import datetime as dt
import os
import tempfile
from contextlib import ExitStack
from pathlib import PurePath as Path
from typing import Any, Sequence
from unittest import mock

from gentoo_build_publisher import publisher as publisher_mod
from gentoo_build_publisher import types as gbp
from gentoo_build_publisher import worker as gbp_worker
from gentoo_build_publisher.publisher import BuildPublisher
from gentoo_build_publisher.records import BuildRecord
from gentoo_build_publisher.settings import Settings as GBPSettings
from unittest_fixtures import FixtureContext, FixtureOptions, Fixtures, depends

from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile, Package


################
# gbp-fl stuff #
################
@depends("tmpdir", "environ")
def settings(_options: FixtureOptions, _fixtures: Fixtures) -> Settings:
    return Settings.from_environ()


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


@depends("now")
def bulk_packages(options: FixtureOptions, fixtures: Fixtures) -> list[Package]:
    packages: list[Package] = []

    for p_def in options.get("bulk_packages", "").strip().split("\n"):
        p_def = p_def.strip()

        if not p_def:
            continue

        parts = p_def.split()
        cpv = parts[0]

        build_id = seq_get(parts, 1, 1)

        try:
            build_time = int(parts[2])
        except IndexError:
            build_time = fixtures.now.timestamp()

        # crude parsing, but good enough for now
        c, pv = cpv.split("/", 1)
        p, v = pv.rsplit("-", 1)
        if v.startswith("r"):
            p, rest = p.rsplit("-", 1)
            v = f"{rest}-{v}"
        path = f"{c}/{p}/{pv}-{build_id}.gpkg.tar"

        package = Package(
            cpv=cpv,
            repo=seq_get(parts, 3, "gentoo"),
            build_id=build_id,
            build_time=build_time,
            path=path,
        )
        packages.append(package)
    return packages


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
def tmpdir(_options: FixtureOptions, _fixtures: Fixtures) -> FixtureContext[Path]:
    with tempfile.TemporaryDirectory() as tempdir:
        yield Path(tempdir)


@depends("tmpdir")
def environ(
    options: FixtureOptions, fixtures: Fixtures
) -> FixtureContext[dict[str, str]]:
    mock_environ = {
        "BUILD_PUBLISHER_API_KEY_ENABLE": "no",
        "BUILD_PUBLISHER_JENKINS_BASE_URL": "https://jenkins.invalid/",
        "BUILD_PUBLISHER_RECORDS_BACKEND": "memory",
        "BUILD_PUBLISHER_STORAGE_PATH": str(fixtures.tmpdir / "gbp"),
        "BUILD_PUBLISHER_WORKER_BACKEND": "sync",
        "BUILD_PUBLISHER_WORKER_THREAD_WAIT": "yes",
        **options.get("environ", {}),
    }
    with mock.patch.dict(os.environ, mock_environ, clear=True):
        yield mock_environ


@depends()
def now(options: FixtureOptions, _fixtures: Fixtures) -> dt.datetime:
    time: dt.datetime = options.get(
        "now", dt.datetime(2025, 1, 26, 12, 57, 37, tzinfo=dt.UTC)
    )
    return time


################################
# gentoo-build-publisher stuff #
################################
@depends("gbp_settings")
def publisher(
    _options: FixtureOptions, fixtures: Fixtures
) -> FixtureContext[BuildPublisher]:
    bp: BuildPublisher = BuildPublisher.from_settings(fixtures.gbp_settings)
    names = ["storage", "jenkins", "repo"]
    module = publisher_mod
    contexts = (
        # pylint: disable=protected-access
        *(mock.patch.object(module._inst, name, getattr(bp, name)) for name in names),
        *(mock.patch.object(module, name, getattr(bp, name)) for name in names),
    )

    with ExitStack() as stack:
        for cm in contexts:
            stack.enter_context(cm)

        yield bp


@depends("gbp_settings")
def worker(
    _options: FixtureOptions, fixtures: Fixtures
) -> FixtureContext[gbp_worker.WorkerInterface]:
    sync_worker = gbp_worker.Worker(fixtures.gbp_settings)
    with mock.patch("gentoo_build_publisher.worker", sync_worker):
        yield sync_worker


@depends("environ")
def gbp_settings(_options: FixtureOptions, _fixtures: Fixtures) -> GBPSettings:
    return GBPSettings.from_environ()


@depends()
def build_record(options: FixtureOptions, _fixtures: Fixtures) -> BuildRecord:
    record = get_options(
        options.get("build_record", {}), build_id="1502", machine="babette", note=None
    )
    return BuildRecord(**record)


@depends("build_record", "now")
def gbp_package(options: FixtureOptions, fixtures: Fixtures) -> gbp.Package:
    pkg_options = get_options(
        options.get("gbp_package", {}),
        build_id=1,
        build_time=fixtures.now.timestamp(),
        cpv="sys-libs/mtdev-1.1.7",
        path="sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
        repo="gentoo",
        size=40960,
    )
    return gbp.Package(**pkg_options)


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


def seq_get(seq: Sequence[Any], index: int, default: Any = None) -> Any:
    """Like dict.get, but for sequences"""
    try:
        return seq[index]
    except IndexError:
        return default
