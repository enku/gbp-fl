"""Tests for the gateway interface"""

# pylint: disable=missing-docstring,unused-argument

from contextlib import ExitStack
from pathlib import PurePath as Path
from unittest import TestCase, mock

import gentoo_build_publisher
from gentoo_build_publisher import types as gtype
from unittest_fixtures import FixtureContext, Fixtures, given

from gbp_fl import gateway as gw
from gbp_fl.types import Build, MissingPackageIdentifier, Package

TESTDIR = Path(__file__).parent


def mock_publisher(_f: Fixtures) -> FixtureContext[dict[str, mock.Mock]]:
    mocks = {"storage": mock.Mock(), "jenkins": mock.Mock(), "repo": mock.Mock()}
    contexts = (
        mock.patch.object(gentoo_build_publisher.publisher, name, value)
        for name, value in mocks.items()
    )

    with ExitStack() as stack:
        for cm in contexts:
            stack.enter_context(cm)

        yield mocks


build = Build(machine="babette", build_id="1442")
package = Package(
    cpv="sys-libs/mtdev-1.1.7",
    repo="gentoo",
    build_id=1,
    build_time=0,
    path="sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
)


@given(mock_publisher)
class GetFullPackagePathTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        mocks = fixtures.mock_publisher
        storage = mocks["storage"]

        storage.get_path.return_value = Path("/binpkgs/babette.1442")
        gbp = gw.GBPGateway()

        full_package_path = gbp.get_full_package_path(build, package)

        self.assertEqual(
            str(full_package_path),
            "/binpkgs/babette.1442/sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
        )


@given(mock_publisher)
class GetPackagesTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        mocks = fixtures.mock_publisher
        storage = mocks["storage"]

        gbp_packages = [
            gtype.Package(
                cpv="sys-libs/mtdev-1.1.7",
                build_id=1,
                repo="gentoo",
                path="/sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
                size=200,
                build_time=0,
            )
        ]
        storage.get_packages.return_value = gbp_packages
        gbp = gw.GBPGateway()

        packages = gbp.get_packages(build)

        expected = [
            Package(
                cpv="sys-libs/mtdev-1.1.7",
                repo="gentoo",
                build_id=1,
                build_time=0,
                path="/sys-libs/mtdev/mtdev-1.1.7-1.gpkg.tar",
            )
        ]
        self.assertEqual(packages, expected)


@given(mock_publisher)
class GetPackageContentsTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        mocks = fixtures.mock_publisher
        storage = mocks["storage"]
        storage.get_path.return_value = TESTDIR / "assets"

        gbp = gw.GBPGateway()
        result = list(gbp.get_package_contents(build, package))

        self.assertEqual(len(result), 19)

    def test_when_empty_tarfile(self, fixtures: Fixtures) -> None:
        gbp = gw.GBPGateway()

        with mock.patch.object(
            gbp, "get_full_package_path", return_value=TESTDIR / "assets/empty.tar"
        ):
            with self.assertRaises(MissingPackageIdentifier):
                list(gbp.get_package_contents(build, package))


class ReceiveSignalTests(TestCase):
    def test(self) -> None:
        dispatcher = mock.Mock()
        receiver = mock.Mock()
        signal = "sos"

        gbp = gw.GBPGateway()

        with mock.patch("gentoo_build_publisher.signals.dispatcher", dispatcher):
            gbp.receive_signal(receiver, signal)

        dispatcher.bind.assert_called_once_with(sos=receiver)


class EmitSignalTests(TestCase):
    def test(self) -> None:
        dispatcher = mock.Mock()
        signal = "sos"

        gbp = gw.GBPGateway()

        with mock.patch("gentoo_build_publisher.signals.dispatcher", dispatcher):
            gbp.emit_signal(signal, buckle_my="shoe")

        dispatcher.emit.assert_called_once_with(signal, buckle_my="shoe")


class RunTaskTests(TestCase):
    def test(self) -> None:
        gbp = gw.GBPGateway()
        func = mock.Mock()

        with mock.patch("gentoo_build_publisher.worker") as worker:
            gbp.run_task(func, 1, 2, buckle_my="shoe")

        worker.run.assert_called_once_with(func, 1, 2, buckle_my="shoe")


class ListMachineNamesTests(TestCase):
    @mock.patch("gentoo_build_publisher.publisher")
    def test(self, publisher: mock.Mock) -> None:
        machines = ["babette", "lighthouse", "polaris"]
        publisher.repo.build_records.list_machines.return_value = machines

        gbp = gw.GBPGateway()

        self.assertEqual(gbp.list_machine_names(), machines)
        publisher.repo.build_records.list_machines.assert_called_once_with()


class GetBuildsForMachineTests(TestCase):
    @mock.patch("gentoo_build_publisher.publisher")
    def test(self, publisher: mock.Mock) -> None:
        builds = [Build(machine="babette", build_id=f"150{i}") for i in range(5)]
        publisher.repo.build_records.for_machine.return_value = iter(builds)

        gbp = gw.GBPGateway()

        self.assertEqual(list(gbp.get_builds_for_machine("babette")), builds)
        publisher.repo.build_records.for_machine.assert_called_once_with("babette")


class GetBuildRecordTests(TestCase):
    @mock.patch("gentoo_build_publisher.publisher")
    def test(self, publisher: mock.Mock) -> None:
        bdict = {"machine": "babette", "build_id": "1507"}
        build_record = mock.Mock(**bdict)
        publisher.repo.build_records.get.return_value = build_record
        gbp = gw.GBPGateway()

        result = gbp.get_build_record(Build(**bdict))

        self.assertEqual(result, build_record)
        publisher.repo.build_records.get.assert_called_once_with(gtype.Build(**bdict))


class SetProcessTests(TestCase):
    @mock.patch("gbp_ps.signals.set_process")
    def test(self, set_process: mock.Mock) -> None:
        gbp = gw.GBPGateway()

        was_set = gbp.set_process(build, "index")

        self.assertTrue(was_set)
        set_process.assert_called_once_with(
            gtype.Build(machine="babette", build_id="1442"), "index"
        )

    @mock.patch("gbp_ps.signals.set_process")
    def test_when_no_gbp_ps_plugin(self, set_process: mock.Mock) -> None:
        gbp = gw.GBPGateway()

        with mock.patch.object(gbp, "has_plugin", return_value=False):
            was_set = gbp.set_process(build, "index")

        self.assertFalse(was_set)
        set_process.assert_not_called()


class HasPluginTests(TestCase):
    def test_true(self) -> None:
        self.assertTrue(gw.GBPGateway.has_plugin("gbp-fl"))

    def test_false(self) -> None:
        self.assertFalse(gw.GBPGateway.has_plugin("bogus"))
