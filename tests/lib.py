"""Test utilities"""

# pylint: disable=missing-docstring,redefined-outer-name

import datetime as dt
import os
from contextlib import contextmanager
from pathlib import PurePath as Path
from tarfile import TarInfo
from typing import Any, Generator, Sequence
from unittest import mock

from gbp_testkit import fixtures as testkit
from gentoo_build_publisher import types as gbp
from gentoo_build_publisher import worker as gbp_worker
from gentoo_build_publisher.cache import cache
from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import (
    STATS_CACHE_KEY,
    BinPkg,
    Build,
    BuildLike,
    ContentFile,
    FileStats,
    MachineStats,
    Package,
)

DEFAULT_CONTENTS = """
    lighthouse 34 app-shells/bash-5.2_p37-1 /bin/bash
    lighthouse 34 app-shells/bash-5.2_p37-1 /etc/skel
    polaris    26 app-arch/tar-1.35-1       /bin/gtar
    polaris    26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris    26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris    27 app-shells/bash-5.2_p37-1 /bin/bash
"""
LOCAL_TIMEZONE = dt.timezone(dt.timedelta(days=-1, seconds=61200), "PDT")
TESTDIR = Path(__file__).parent


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


@fixture(testkit.tmpdir)
def environ(
    fixtures: Fixtures, environ: dict[str, str] | None = None
) -> FixtureContext[dict[str, str]]:
    mock_environ = {
        **next(testkit.environ(fixtures), {}),
        "BUILD_PUBLISHER_API_KEY_ENABLE": "no",
        "BUILD_PUBLISHER_JENKINS_BASE_URL": "https://jenkins.invalid/",
        "BUILD_PUBLISHER_RECORDS_BACKEND": "memory",
        "BUILD_PUBLISHER_STORAGE_PATH": str(fixtures.tmpdir / "gbp"),
        "BUILD_PUBLISHER_WORKER_BACKEND": "sync",
        "BUILD_PUBLISHER_WORKER_THREAD_WAIT": "yes",
        "GBP_FL_RECORDS_BACKEND": "memory",
        **(environ or {}),
    }
    with mock.patch.dict(os.environ, mock_environ):
        yield mock_environ


@fixture(testkit.tmpdir, environ)
def fl_settings(_fixtures: Fixtures) -> Settings:
    return Settings.from_environ()


@fixture(fl_settings)
def repo(fixtures: Fixtures, repo: str = "gbp_fl.records.Repo") -> FixtureContext[Repo]:
    Repo.from_settings.cache_clear()
    repo_ = Repo.from_settings(fixtures.fl_settings)

    with mock.patch(f"{repo}.from_settings", return_value=repo_):
        yield repo_


@fixture()
def now(
    _fixtures: Fixtures,
    now: dt.datetime = dt.datetime(2025, 1, 26, 12, 57, 37, tzinfo=dt.UTC),
) -> dt.datetime:
    return now


@fixture()
def build(_fixtures: Fixtures, build: str = "lighthouse.34") -> Build:
    machine, build_id = build.split(".", 1)

    return Build(machine=machine, build_id=build_id)


@fixture(build, now)
def binpkg(  # pylint: disable=too-many-arguments
    fixtures: Fixtures,
    build: Build | None = None,
    cpvb: str = "app-shells/bash-5.2_p37-3",
    build_time: dt.datetime | None = None,
    repo: str = "gentoo",
) -> BinPkg:
    return BinPkg(
        build=build or fixtures.build,
        cpvb=cpvb,
        build_time=build_time or fixtures.now,
        repo=repo,
    )


@fixture(binpkg, now)
def content_file(
    fixtures: Fixtures,
    binpkg: BinPkg | None = None,
    path: Path = Path("/bin/bash"),
    timestamp: dt.datetime | None = None,
    size: int = 870400,
) -> ContentFile:
    return ContentFile(
        binpkg=binpkg or fixtures.binpkg,
        path=path,
        timestamp=timestamp or fixtures.now,
        size=size,
    )


@fixture(now)
def bulk_content_files(
    fixtures: Fixtures, bulk_content_files: str = DEFAULT_CONTENTS
) -> list[ContentFile]:
    content_files: list[ContentFile] = []
    cf_defs: str = bulk_content_files.strip()
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


@fixture(now)
def bulk_packages(fixtures: Fixtures, bulk_packages: str = "") -> list[Package]:
    packages: list[Package] = []

    for p_def in (bulk_packages or "").strip().split("\n"):
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


@fixture(testkit.build_record, now)
def gbp_package(  # pylint: disable=too-many-arguments
    fixtures: Fixtures,
    *,
    build_id: int = 1,
    build_time: int | None = None,
    cpv: str = "sys-libs/mtdev-1.1.7",
    path: str = "sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
    repo: str = "gentoo",
    size: int = 40960,
) -> gbp.Package:
    build_time = build_time or fixtures.now.timestamp()
    record = fixtures.build_record
    return gbp.Package(
        build_id=build_id,
        build_time=build_time,
        cpv=cpv,
        path=path,
        repo=repo,
        size=size,
        build=gbp.Build(record.machine, record.build_id),
    )


@fixture(testkit.settings)
def worker(fixtures: Fixtures) -> FixtureContext[gbp_worker.WorkerInterface]:
    sync_worker = gbp_worker.Worker(fixtures.settings)
    with mock.patch("gentoo_build_publisher.worker", sync_worker):
        yield sync_worker


def seq_get(seq: Sequence[Any], index: int, default: Any = None) -> Any:
    """Like dict.get, but for sequences"""
    try:
        return seq[index]
    except IndexError:
        return default


@fixture()
def gateway(_: Fixtures) -> MockGBPGateway:
    return MockGBPGateway()


@fixture()
def tarinfo(_: Fixtures, name: str = "image/bin/bash") -> mock.Mock:
    mock_tarinfo = mock.Mock(mtime=0, size=22)
    mock_tarinfo.isdir.return_value = False
    mock_tarinfo.name = name

    return mock_tarinfo


@fixture()
def package(
    _: Fixtures,
    cpv: str = "sys-libs/mtdev-1.1.7",
    repo: str = "gentoo",
    build_id: int = 1,
    build_time: int = 10,
    path: str = "sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
) -> Package:
    return Package(
        cpv=cpv, repo=repo, build_id=build_id, build_time=build_time, path=path
    )


@fixture()
def stats(_: Fixtures) -> FileStats:
    return FileStats(
        total=9605802 + 9540343,
        by_machine={
            "polaris": MachineStats(total=9605802, build_count=33),
            "lighthouse": MachineStats(total=9540343, build_count=35),
        },
    )


@fixture(stats)
def cached_stats(fixtures: Fixtures) -> None:
    cache.clear()
    cache.set(STATS_CACHE_KEY, fixtures.stats)
