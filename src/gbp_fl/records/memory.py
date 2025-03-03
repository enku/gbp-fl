"""memory-based ContentFiles backend"""

import fnmatch
from dataclasses import replace
from pathlib import PurePath as Path
from typing import Any, Iterable

from gbp_fl.types import ContentFile

from . import RecordNotFound


class ContentFiles:
    """Memory-backed ContentFiles repo"""

    def __init__(self) -> None:
        # [machine, build_id, cpvb, path, package_build_id] = ContentFile
        self.files: dict[tuple[str, str, str, str], ContentFile] = {}

    def save(self, content_file: ContentFile, **fields: Any) -> ContentFile:
        """Save the given ContentFile with given updated fields

        Return the updated ContentFile
        """
        files = self.files
        new = replace(content_file, **fields)

        try:
            self.delete(content_file)
        except RecordNotFound:
            pass

        binpkg = new.binpkg
        build = binpkg.build
        files[build.machine, build.build_id, binpkg.cpvb, str(new.path)] = new

        return new

    def bulk_save(self, content_files: Iterable[ContentFile]) -> None:
        """Bulk save a list of ContentFiles"""
        for content_file in content_files:
            self.save(content_file)

    def get(
        self, machine: str, build_id: str, cpvb: str, path: str | Path
    ) -> ContentFile:
        """Return the ContentFile with the given properties

        If no ContentFile matches, raise RecordNotFound
        """
        path = str(path)
        files = self.files
        if record := files.get((machine, build_id, cpvb, path), None):
            return record

        raise RecordNotFound()

    def delete(self, content_file: ContentFile) -> None:
        """Delete the given ContentFile from the database

        Raise RecordNotFound if it doesn't exist in the database.
        """
        files = self.files

        binpkg = content_file.binpkg
        build = binpkg.build
        try:
            del files[
                build.machine, build.build_id, binpkg.cpvb, str(content_file.path)
            ]
        except KeyError:
            raise RecordNotFound() from None

    def deindex_build(self, machine: str, build_id: str) -> None:
        """Delete all content files for the given build"""
        match = (machine, build_id)
        files = self.files
        keys = tuple(files)

        for key in keys:
            if key[:2] == match:
                del files[key]

    def exists(self, machine: str, build_id: str, cpvb: str, path: str | Path) -> bool:
        """Return true if a package file with matching criteria exists in the db"""
        try:
            self.get(machine, build_id, cpvb, path)
            return True
        except RecordNotFound:
            return False

    def count(self, machine: str | None, build_id: str | None, cpvb: str | None) -> int:
        """Return the number of package files exist with the given critiria

        When the following parameters are not None:

        - machine: the number of files for the given machine
        - machine and build_id: the number of files for the given build
        - machine, build_id, and cpvb: the number of files for the given build's package

        When all parameters are none, returns the total number of package files on GBP

        All other combinations raise ValueError
        """
        params = {"machine": machine, "build_id": build_id, "cpvb": cpvb}
        query: tuple[str, ...] = ()

        previous = ""
        for i, (field, value) in enumerate(params.items()):
            if value:
                if len(query) < i:
                    raise ValueError(f"Must supply {previous} if supplying {field}")
                query = (*query, value)
            previous = field

        item_count = len(query)
        return sum(1 for record in self.files if record[:item_count] == query)

    def for_package(
        self, machine: str, build_id: str, cpvb: str
    ) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build and cpvb"""
        files = self.files.copy()
        for key, content_file in files.items():
            if key[:3] == (machine, build_id, cpvb):
                yield content_file

    def for_build(self, machine: str, build_id: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build"""
        files = self.files.copy()
        for key, content_file in files.items():
            if key[:2] == (machine, build_id):
                yield content_file

    def for_machine(self, machine: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given machine"""
        files = self.files.copy()
        for key, content_file in files.items():
            if key[0] == machine:
                yield content_file

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
        if not key:
            return

        matcher = path_basename_checker

        if "/" in key:
            matcher = exact_match_checker
        elif "*" in key:
            matcher = glob_checker

        for content_file in self.files.values():
            if machine and content_file.binpkg.build.machine != machine:
                continue
            if matcher(content_file, key):
                yield content_file


def exact_match_checker(content_file: ContentFile, key: str) -> bool:
    """Return True if key matches the exact path for the given ContentFile

    Otherwise return False.
    """
    if key[0] != "/":
        key = f"/{key}"

    return str(content_file.path) == key


def path_basename_checker(content_file: ContentFile, key: str) -> bool:
    """Return True if key matches the exact basename for the given ContentFile

    Otherwise return False.
    """
    return content_file.path.name == key


def glob_checker(content_file: ContentFile, key: str) -> bool:
    """Return True if key is a glob match for the basename of the given ContentFile

    Otherwise return False.
    """
    basename = content_file.path.name

    return fnmatch.fnmatch(basename, key)
