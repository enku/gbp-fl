# pylint: disable=missing-docstring
import datetime as dt
import os
from pathlib import PurePath as Path
from typing import Any, Sequence
from unittest import mock

from gbp_testkit import fixtures as testkit
from gbp_testkit import helpers
from gbpcli.gbp import GBP
from gentoo_build_publisher import types as gbp
from gentoo_build_publisher import worker as gbp_worker
from unittest_fixtures import FixtureContext, FixtureOptions, Fixtures, depends

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile, Package

client = testkit.client
console = testkit.console
publisher = testkit.publisher
record = testkit.record
server_settings = testkit.settings
tmpdir = testkit.tmpdir


@depends()
def gbp_client(options: FixtureOptions, _fixtures: Fixtures) -> GBP:
    url: str = options.get("gbp_client", {}).get("url", "http://gbp.invalid/")

    return helpers.test_gbp(url)


@depends("tmpdir")
def environ(
    options: FixtureOptions, fixtures: Fixtures
) -> FixtureContext[dict[str, str]]:
    mock_environ = {
        **next(testkit.environ(options, fixtures), {}),
        "BUILD_PUBLISHER_API_KEY_ENABLE": "no",
        "BUILD_PUBLISHER_JENKINS_BASE_URL": "https://jenkins.invalid/",
        "BUILD_PUBLISHER_RECORDS_BACKEND": "memory",
        "BUILD_PUBLISHER_STORAGE_PATH": str(fixtures.tmpdir / "gbp"),
        "BUILD_PUBLISHER_WORKER_BACKEND": "sync",
        "BUILD_PUBLISHER_WORKER_THREAD_WAIT": "yes",
        "GBP_FL_RECORDS_BACKEND": "memory",
        **options.get("environ", {}),
    }
    with mock.patch.dict(os.environ, mock_environ):
        yield mock_environ


@depends("tmpdir", "environ")
def settings(_options: FixtureOptions, _fixtures: Fixtures) -> Settings:
    return Settings.from_environ()


@depends("settings")
def repo(options: FixtureOptions, fixtures: Fixtures) -> FixtureContext[Repo]:
    where: str = options.get("repo", {}).get("where", "gbp_fl.records.Repo")
    repo_: Repo = Repo.from_settings(fixtures.settings)

    with mock.patch(f"{where}.from_settings", return_value=repo_):
        yield repo_


@depends()
def now(options: FixtureOptions, _fixtures: Fixtures) -> dt.datetime:
    time: dt.datetime = options.get(
        "now", dt.datetime(2025, 1, 26, 12, 57, 37, tzinfo=dt.UTC)
    )
    return time


@depends()
def build(options: FixtureOptions, _fixtures: Fixtures) -> Build:
    args = get_options(options.get("build", {}), machine="lighthouse", build_id="34")

    return Build(**args)


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

        try:
            size = int(parts[5])
        except IndexError:
            size = 850648

        try:
            timestamp = dt.datetime.fromisoformat(parts[6]).astimezone(dt.UTC)
        except IndexError:
            timestamp = fixtures.now

        bld = Build(machine=machine, build_id=build_id)
        pkg = BinPkg(build=bld, cpvb=cpvb, build_time=fixtures.now, repo=repo_)
        content_files.append(
            ContentFile(
                binpkg=pkg, path=Path(path), timestamp=timestamp, size=int(size)
            )
        )

    return content_files


DEFAULT_CONTENTS = """
    lighthouse 34 app-shells/bash-5.2_p37-1 /bin/bash
    lighthouse 34 app-shells/bash-5.2_p37-1 /etc/skel
    polaris    26 app-arch/tar-1.35-1       /bin/gtar
    polaris    26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris    26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris    27 app-shells/bash-5.2_p37-1 /bin/bash
"""


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


@depends("record", "now")
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


@depends(settings="server_settings")
def worker(
    _options: FixtureOptions, fixtures: Fixtures
) -> FixtureContext[gbp_worker.WorkerInterface]:
    sync_worker = gbp_worker.Worker(fixtures.settings)
    with mock.patch("gentoo_build_publisher.worker", sync_worker):
        yield sync_worker


def get_options(options: FixtureOptions, **defaults: Any) -> FixtureOptions:
    return {item: options.get(item, default) for item, default in defaults.items()}


def seq_get(seq: Sequence[Any], index: int, default: Any = None) -> Any:
    """Like dict.get, but for sequences"""
    try:
        return seq[index]
    except IndexError:
        return default
