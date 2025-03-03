"""Django ORM-backed records backend"""

import os.path
from dataclasses import replace
from pathlib import PurePath as Path
from typing import Any, Iterable

from django.db import transaction

from gbp_fl import models
from gbp_fl.records import RecordNotFound
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile

BULK_BATCH_SIZE = 100


class ContentFiles:
    """Django ORM-backed repository for Package files"""

    def save(self, content_file: ContentFile, **fields: Any) -> ContentFile:
        """Save the given ContentFile with given updated fields

        Return the updated ContentFile
        """
        new = replace(content_file, **fields)
        model = content_file_to_model(new)

        try:
            self.delete(content_file)
        except RecordNotFound:
            pass

        model.save()

        return new

    @transaction.atomic()
    def bulk_save(self, content_files: Iterable[ContentFile]) -> None:
        """Bulk save a list of ContentFiles"""
        get_basename = os.path.basename
        manager = models.ContentFile.objects
        settings = Settings.from_environ()
        batch_size = settings.RECORDS_BACKEND_DJANGO_BULK_BATCH_SIZE

        items = manager.bulk_create(
            (content_file_to_model(cf) for cf in content_files), batch_size=batch_size
        )
        for item in items:
            item.basename = get_basename(item.path)
        manager.bulk_update(items, ["basename"], batch_size=batch_size)

    def get(
        self, machine: str, build_id: str, cpvb: str, path: str | Path
    ) -> ContentFile:
        """Return the ContentFile with the given properties

        If no ContentFile matches, raise RecordNotFound
        """
        model = get_model(machine, build_id, cpvb, path)
        return model_to_content_file(model)

    def delete(self, content_file: ContentFile) -> None:
        """Delete the given ContentFile from the database

        Raise RecordNotFound if it doesn't exist in the database.
        """
        model = get_model(
            content_file.binpkg.build.machine,
            content_file.binpkg.build.build_id,
            content_file.binpkg.cpvb,
            content_file.path,
        )
        model.delete()

    def deindex_build(self, machine: str, build_id: str) -> None:
        """Delete all content files for the given build"""
        manager = models.ContentFile.objects

        manager.filter(machine=machine, build_id=build_id).delete()

    def exists(self, machine: str, build_id: str, cpvb: str, path: str | Path) -> bool:
        """Return true if a package file with matching criteria exists in the db"""
        manager = models.ContentFile.objects
        query = manager.filter(
            machine=machine, build_id=build_id, cpvb=cpvb, path=str(path)
        )
        return query.exists()

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
        query_dict: dict[str, Any] = {}

        previous = ""
        for field, value in params.items():
            if value:
                if previous and previous not in query_dict:
                    raise ValueError(f"Must supply {previous} if supplying {field}")
                query_dict[field] = value
            previous = field

        return models.ContentFile.objects.filter(**query_dict).count()

    def for_package(
        self, machine: str, build_id: str, cpvb: str
    ) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build and cpvb"""
        query = models.ContentFile.objects.filter(
            machine=machine, build_id=build_id, cpvb=cpvb
        )
        yield from (model_to_content_file(model) for model in query)

    def for_build(self, machine: str, build_id: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given build"""
        query = models.ContentFile.objects.filter(machine=machine, build_id=build_id)

        yield from (model_to_content_file(model) for model in query)

    def for_machine(self, machine: str) -> Iterable[ContentFile]:
        """Return all ContentFiles for the given machine"""
        query = models.ContentFile.objects.filter(machine=machine)

        yield from (model_to_content_file(model) for model in query)

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
              backend and are not guaranteed to provided the expected matches.
        """
        if not key:
            return

        query_dict = {"machine": machine} if machine is not None else {}

        if "/" in key:
            if key[0] != "/":
                key = f"/{key}"
            query_dict["path"] = key
        elif key.startswith("*") and key.endswith("*"):
            query_dict["basename__contains"] = key.strip("*")
        elif key.startswith("*"):
            query_dict["basename__endswith"] = key.lstrip("*")
        elif key.endswith("*"):
            query_dict["basename__startswith"] = key.rstrip("*")
        else:
            query_dict["basename"] = key

        query = models.ContentFile.objects.filter(**query_dict)

        yield from (model_to_content_file(model) for model in query)


def get_model(
    machine: str, build_id: str, cpvb: str, path: Path | str
) -> models.ContentFile:
    """Return the Django model matching the given parameters

    If no model exists, raise RecordNotFound.
    """
    try:
        return models.ContentFile.objects.get(
            machine=machine, build_id=build_id, cpvb=cpvb, path=str(path)
        )
    except models.ContentFile.DoesNotExist:
        raise RecordNotFound from None


def content_file_to_model(content_file: ContentFile) -> models.ContentFile:
    """Convert the given ContentFile to a ContentFile Django model

    The model returned unsaved.
    """
    model = models.ContentFile()
    model.machine = content_file.binpkg.build.machine
    model.build_id = content_file.binpkg.build.build_id
    model.path = str(content_file.path)
    model.cpvb = content_file.binpkg.cpvb
    model.repo = content_file.binpkg.repo
    model.size = content_file.size
    model.timestamp = content_file.timestamp

    return model


def model_to_content_file(model: models.ContentFile) -> ContentFile:
    """Convert the given ContentFile Django model to the ContentFile dataclass"""
    build = Build(machine=model.machine, build_id=model.build_id)
    binpkg = BinPkg(
        cpvb=model.cpvb, build=build, build_time=model.timestamp, repo=model.repo
    )
    content_file = ContentFile(
        path=Path(model.path), binpkg=binpkg, timestamp=model.timestamp, size=model.size
    )
    return content_file
