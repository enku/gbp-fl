"""DB interface for gbp-fl"""

import importlib.metadata
from dataclasses import dataclass
from pathlib import PurePath as Path
from typing import Any, Iterable, Protocol, Self, cast

from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile


class RecordNotFound(LookupError):
    """Exception raised when a requested record was not found"""


class ContentFiles(Protocol):  # pragma: no cover
    """Repository for Package files"""

    def save(self, content_file: ContentFile, **fields: Any) -> ContentFile:
        """Save the given ContentFile with given updated fields

        Return the updated ContentFile
        """

    def bulk_save(self, content_files: Iterable[ContentFile]) -> None:
        """Bulk save a list of ContentFiles"""

    def get(
        self, machine: str, build_id: str, cpvb: str, path: str | Path
    ) -> ContentFile:
        """Return the ContentFile with the given properties

        If no ContentFile matches, raise RecordNotFound
        """

    def delete(self, content_file: ContentFile) -> None:
        """Delete the given ContentFile from the database

        Raise RecordNotFound if it doesn't exist in the database.
        """

    def delete_from_build(self, machine: str, build_id: str) -> None:
        """Delete all content files for the given build"""

    def exists(self, machine: str, build_id: str, cpvb: str, path: str | Path) -> bool:
        """Return true if a package file with matching criteria exists in the db"""

    def count(self, machine: str | None, build_id: str | None, cpvb: str | None) -> int:
        """Return the number of package files exist with the given critiria

        When the following parameters are not None:

        - machine: the number of files for the given machine
        - machine and build_id: the number of files for the given build
        - machine, build_id, and cpv: the number of files for the given build's package

        When all parameters are none, returns the total number of package files on GBP

        All other combinations raise ValueError
        """

    def for_package(
        self, machine: str, build_id: str, cpvb: str
    ) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build and cpv"""

    def for_build(self, machine: str, build_id: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build"""

    def for_machine(self, machine: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given machine"""

    def search(self, key: str, machine: str | None = None) -> Iterable[ContentFile]:
        """Search the database for package files

        If machine is provided, restrict the search to files belonging to the given
        machine.

        The simple search key works like the following:

            - A key without "*" or "/" characters searches an exact match on the file's
              base name. For example if the key is "bash" then it matches "/bin/bash"
              but not "/usr/bin/bashbug"

            - Keys containing at least one "/" are interpreted as exact path matches.
              For example the key "/bin/bash" matches files whose path is exactly
              "/bin/bash". If the key does not start with a forward slash then it is
              automatically prepended.

            - Keys with an asterisk either at the start and/or end of the key perform
              wildcard matches but only on the basename of the file. For example the key
              "b*" matches "/bin/bash" and "/usr/bin/bashbug" but not
              "/usr/share/baselayout/fstab". Keys with an asterisk in the middle depend
              on the backend and are not guaranteed to provide the expected matches.

            - A key that's the empty string ("") matches nothing.

            - A key that contains nothing bug asterisks (e.g. "*") depends on the
              backend and are not guaranteed to provide the expected matches.
        """


def files_backend(backend: str) -> ContentFiles:
    """Load the ContentFiles db interface given the settings"""
    try:
        [module] = importlib.metadata.entry_points(group="gbp_fl.records", name=backend)
    except ValueError:
        raise LookupError(f"RECORDS_BACKEND not found: {backend}") from None

    return cast(ContentFiles, module.load().ContentFiles())


@dataclass(frozen=True)
class Repo:
    """Repository pattern"""

    files: ContentFiles

    @classmethod
    def from_settings(cls: type[Self], settings: Settings) -> Self:
        """Return instance of the Repo class given in settings"""
        return cls(files=files_backend(settings.RECORDS_BACKEND))
