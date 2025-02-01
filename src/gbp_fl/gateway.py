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
access gbp-local attributes or else type checkers will hollar.
"""

from pathlib import PurePath as Path
from tarfile import TarFile, TarInfo
from typing import Any, Callable, Iterator, ParamSpec

from pydispatch import Dispatcher  # type: ignore

from gbp_fl.types import Build, Package

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
            # We're not sure of the exact filename of the inner tarfile because of available
            # compression options, but we know what the name starts with.
            # https://www.gentoo.org/glep/glep-0078.html#the-container-format
            pv = package.cpv.partition("/")[2]
            prefix = f"{pv}-{package.build_id}/image.tar"

            for item in tarfile:
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

    @property
    def _dispatcher(self) -> Dispatcher:
        """Return the GBP signal dispatcher.

        Warning: this method leaks!
        """
        from gentoo_build_publisher import signals

        return signals.dispatcher
