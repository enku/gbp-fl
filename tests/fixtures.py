# pylint: disable=missing-docstring,redefined-outer-name
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
from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile, Package

from .utils import MockGBPGateway

build_model = testkit.build_model
client = testkit.client
console = testkit.console
publisher = testkit.publisher
record = testkit.record
records_db = testkit.records_db
server_settings = testkit.settings
tmpdir = testkit.tmpdir


DEFAULT_CONTENTS = """
    lighthouse 34 app-shells/bash-5.2_p37-1 /bin/bash
    lighthouse 34 app-shells/bash-5.2_p37-1 /etc/skel
    polaris    26 app-arch/tar-1.35-1       /bin/gtar
    polaris    26 app-shells/bash-5.2_p37-1 /bin/bash
    polaris    26 app-shells/bash-5.2_p37-2 /bin/bash
    polaris    27 app-shells/bash-5.2_p37-1 /bin/bash
"""
LOCAL_TIMEZONE = dt.timezone(dt.timedelta(days=-1, seconds=61200), "PDT")


@fixture()
def gbp_client(_fixtures: Fixtures, url: str = "http://gbp.invalid/") -> GBP:
    return helpers.test_gbp(url)


@fixture("tmpdir")
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


@fixture("tmpdir", "environ")
def settings(_fixtures: Fixtures) -> Settings:
    return Settings.from_environ()


@fixture("settings")
def repo(fixtures: Fixtures, repo: str = "gbp_fl.records.repo") -> FixtureContext[Repo]:
    repo_: Repo = Repo.from_settings(fixtures.settings)

    with mock.patch(repo, new=repo_):
        yield repo_


@fixture()
def now(
    _fixtures: Fixtures,
    now: dt.datetime = dt.datetime(2025, 1, 26, 12, 57, 37, tzinfo=dt.UTC),
) -> dt.datetime:
    return now


@fixture()
def build(
    _fixtures: Fixtures, machine: str = "lighthouse", build_id: str = "34"
) -> Build:
    return Build(machine=machine, build_id=build_id)


@fixture("build", "now")
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


@fixture("binpkg", "now")
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


@fixture("now")
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


@fixture("now")
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


@fixture("record", "now")
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
    return gbp.Package(
        build_id=build_id,
        build_time=build_time,
        cpv=cpv,
        path=path,
        repo=repo,
        size=size,
    )


@fixture(settings="server_settings")
def worker(fixtures: Fixtures) -> FixtureContext[gbp_worker.WorkerInterface]:
    sync_worker = gbp_worker.Worker(fixtures.settings)
    with mock.patch("gentoo_build_publisher.worker", sync_worker):
        yield sync_worker


def get_options(options: dict[str, Any] | None, **defaults: Any) -> dict[str, Any]:
    options = options or {}
    return {item: options.get(item, default) for item, default in defaults.items()}


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
def local_timezone(
    _: Fixtures, local_timezone: dt.timezone = LOCAL_TIMEZONE
) -> FixtureContext[dt.timezone]:
    with mock.patch("gbpcli.render.LOCAL_TIMEZONE", new=local_timezone):
        yield local_timezone


@fixture()
def tarinfo(_: Fixtures, name: str = "image/bin/bash") -> mock.Mock:
    mock_tarinfo = mock.Mock(mtime=0, size=22)
    mock_tarinfo.isdir.return_value = False
    mock_tarinfo.name = name

    return mock_tarinfo
