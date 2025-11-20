"""Gateway to the Gentoo Build Publisher

The rationale here is not to expose Gentoo Build Publisher internals to the rest of
gbp-fl, even though we're using the public interface. I want to do this because I don't
want the rest of gbp-fl importing modules from gentoo_build_publisher. In django there's
this ongoing risk with app dependencies where you might encounter either circular deps
or apps not ready and I want to at least put all that risk in one place.

The GBPGateway here talks to GBP, however each method is responsible for importing what
parts of GBP it needs form *inside* the method itself. In addition methods are required
to only accept gbp-fl-local types and only return gbp-fl-local times. One exception is
the GBP signal receiver functions which will naturally receive gbp-internal types.
However there are wrapper types in gbp_fl.types so that receivers can at least only
access gbp-local attributes or else type checkers will holler.
"""

from contextlib import contextmanager
from pathlib import PurePath as Path
from tarfile import TarFile, TarInfo
from typing import TYPE_CHECKING, Any, Callable, Iterator, ParamSpec, cast

from gbp_fl import utils
from gbp_fl.records import Repo
from gbp_fl.types import Build, BuildLike, FileStats, MissingPackageIdentifier, Package

if TYPE_CHECKING:
    from gentoo_build_publisher import signals

P = ParamSpec("P")


class GBPGateway:
    """The GBP Gateway

    Methods should only accept gbp-fl types and only return gbp-fl types.
    """

    # pylint: disable=import-outside-toplevel
    def receive_signal(self, receiver: Callable[..., Any], signal: str) -> None:
        """Register the given signal receiver with the given GBP signal

        Receivers may receive GBP data types and are encourage to convert them to gbp-fl
        data types immediately.
        """
        dispatcher = self._dispatcher
        dispatcher.bind(**{signal: receiver})

    def emit_signal(self, signal: str, **kwargs: Any) -> None:
        """Emit signal on the gbp dispatcher

        This is mainly used for testing
        """
        dispatcher = self._dispatcher
        dispatcher.emit(signal, **kwargs)

    def register_signal(self, name: str) -> None:
        """Register the given signal with GBP's dispatcher"""
        dispatcher = self._dispatcher
        dispatcher.register_event(name)

    def list_machine_names(self) -> list[str]:
        """Return the list of machines that GBP holds builds for"""
        from gentoo_build_publisher import publisher

        repo = publisher.repo

        return repo.build_records.list_machines()

    def get_builds_for_machine(self, machine: str) -> Iterator[Build]:
        """Return the builds for the given machine"""
        from gentoo_build_publisher import publisher

        repo = publisher.repo

        return (
            Build(machine=build.machine, build_id=build.build_id)
            for build in repo.build_records.for_machine(machine)
        )

    def get_build_record(self, build: Build) -> BuildLike:
        """Return the build record given the build

        Internally we should only treat this like a BuildLike, however GraphQL may treat
        it like a GBP BuildRecord.
        """
        from gentoo_build_publisher import publisher
        from gentoo_build_publisher.types import Build as GBPBuild

        build_records = publisher.repo.build_records

        record = build_records.get(
            GBPBuild(machine=build.machine, build_id=build.build_id)
        )

        # I dont' think you should need to cast but mypy begs to differ
        return cast(BuildLike, record)

    def get_full_package_path(self, build: Build, package: Package) -> Path:
        """Return the full path of the given Package"""
        from gentoo_build_publisher import publisher, types

        storage = publisher.storage
        b = types.Build(machine=build.machine, build_id=build.build_id)
        binpkgs_path = storage.get_path(b, types.Content.BINPKGS)

        return binpkgs_path / package.path

    def get_packages(self, build: Build) -> list[Package]:
        """Return all the Packages contained in the given Build"""
        from gentoo_build_publisher import publisher, types

        storage = publisher.storage
        gbp_build = types.Build(machine=build.machine, build_id=build.build_id)

        return [
            Package(
                cpv=p.cpv,
                repo=p.repo,
                path=p.path,
                build_id=p.build_id,
                build_time=p.build_time,
            )
            for p in storage.get_packages(gbp_build)
        ]

    def get_package_contents(self, build: Build, package: Package) -> Iterator[TarInfo]:
        """Given the build and binary package, return the packages contents

        This scours the binary tarball for package files.
        Generates tarfile.TarInfo objects.
        """
        package_path = self.get_full_package_path(build, package)

        with TarFile.open(package_path, "r") as tarfile:
            try:
                utils.ensure_package_identifier(package, tarfile)
            except MissingPackageIdentifier:
                yield from tarfile.getmembers()

            # We're not sure of the exact filename of the inner tarfile because of
            # available compression options, but we know what the name starts with.
            # https://www.gentoo.org/glep/glep-0078.html#the-container-format
            pv = package.cpv.partition("/")[2]
            prefix = f"{pv}-{package.build_id}/image.tar"

            for item in tarfile:  # pragma: no branch
                if item.name.startswith(prefix):
                    image_fp = tarfile.extractfile(item)
                    # this is also a tarfile
                    with TarFile.open(mode="r", fileobj=image_fp) as image:
                        yield from image.getmembers()
                    break

    def run_task(
        self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        """Send the given callable (and args to the GBP task worker to run"""
        from gentoo_build_publisher import worker

        worker.run(func, *args, **kwargs)

    def _really_set_process(self, build: Build, phase: str) -> None:
        """Unconditionally set the current process state for the given build"""
        from gbp_ps.signals import set_process
        from gentoo_build_publisher import types

        gbp_build = types.Build(machine=build.machine, build_id=build.build_id)
        set_process(gbp_build, phase)

    @contextmanager
    def set_process(self, build: Build, phase: str) -> Iterator[bool]:
        """Conditinally set the current process state for the given build

        When entered, sets the process to the given phase, when exited, set's the
        process phase to "clean".

        If the gbp-ps plugin is not installed, this is a noop.

        Yield True if the process was set, otherwise yield False.
        """
        if self.has_plugin("gbp-ps"):
            self._really_set_process(build, phase)
            yield True
            self._really_set_process(build, "clean")
        else:
            yield False

    def get_file_stats(self, repo: Repo) -> FileStats:
        """Calculate the current file stats from the Repo"""
        builds_per_machine = {
            machine: sum(1 for _ in self.get_builds_for_machine(machine))
            for machine in self.list_machine_names()
        }
        return FileStats.collect(repo.files, builds_per_machine)

    def get_cached_stats(self) -> FileStats | None:
        """Return the cached FileStats

        If no FileStats are cached, return None.
        """
        from gentoo_build_publisher.cache import cache

        fl_cache = cache / "fl"

        return cast(FileStats | None, fl_cache.get("stats"))

    def set_cached_stats(self, stats: FileStats) -> None:
        """Save the given FileStats to the cache"""
        from gentoo_build_publisher.cache import cache

        fl_cache = cache / "fl"

        fl_cache.set("stats", stats)

    @staticmethod
    def has_plugin(name: str) -> bool:
        """Return true if gbp has the given plugin"""
        from gentoo_build_publisher import plugins

        return any(plugin.name == name for plugin in plugins.get_plugins())

    @property
    def _dispatcher(self) -> "signals.PublisherDispatcher":
        """Return the GBP signal dispatcher.

        Warning: this method leaks!
        """
        from gentoo_build_publisher import signals

        return signals.dispatcher


gateway = GBPGateway()
