# pylint: disable=missing-docstring,unused-argument

import datetime as dt
import inspect
from functools import partial
from importlib import import_module
from pathlib import PurePath as Path

from django.test import TestCase
from unittest_fixtures import Fixtures, given, params

from gbp_fl.records import ContentFiles, RecordNotFound, Repo, django_orm, files_backend
from gbp_fl.settings import Settings
from gbp_fl.types import ContentFile

from . import lib

now = partial(dt.datetime.now, tz=dt.UTC)

BACKENDS = ("memory", "django")


@params(backend_type=BACKENDS)
@given(files=lambda f: files_backend(f.backend_type))
@given(lib.content_file, lib.bulk_content_files)
class ContentFilesTests(TestCase):
    # pylint: disable=too-many-public-methods
    def test_supports_protocol(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        cls = type(files)
        alias = f"{cls.__module__}:{cls.__name__}"

        for name, prop in ContentFiles.__dict__.items():
            if name.startswith("_"):
                continue

            if callable(prop):
                self.assertTrue(
                    hasattr(cls, name), f"{alias} should have method {name}"
                )
                self.assertTrue(callable(prop), f"{alias}.{name} should be callable")
                prot_sig = inspect.signature(prop)
                cls_sig = inspect.signature(getattr(cls, name))
                self.assertEqual(
                    prot_sig, cls_sig, f"{alias}.{name} has the wrong signature"
                )
            else:
                self.assertIs(type(prop), type(getattr(cls, name)))

    def test_save(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        content_file: ContentFile = fixtures.content_file

        files.save(content_file)

        record = files.get(
            content_file.binpkg.build.machine,
            content_file.binpkg.build.build_id,
            content_file.binpkg.cpvb,
            content_file.path,
        )

        self.assertIsInstance(record, ContentFile)
        self.assertEqual(record, content_file)

    def test_bulk_save(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        content_files = fixtures.bulk_content_files

        files.bulk_save(content_files)

        self.assertEqual(files.count(None, None, None), 6)

    def test_get(self, fixtures: Fixtures) -> None:
        content_file = fixtures.content_file
        files = fixtures.files

        files.save(content_file)

        binpkg = content_file.binpkg
        build = binpkg.build
        record = files.get(
            build.machine, build.build_id, binpkg.cpvb, content_file.path
        )

        self.assertEqual(record, content_file)

    def test_get_not_found(self, fixtures: Fixtures) -> None:
        content_file = fixtures.content_file
        files = fixtures.files

        binpkg = content_file.binpkg
        build = binpkg.build
        with self.assertRaises(RecordNotFound):
            files.get(build.machine, build.build_id, binpkg.cpvb, content_file.path)

    def test_delete(self, fixtures: Fixtures) -> None:
        content_file = fixtures.content_file
        files = fixtures.files
        files.save(content_file)

        files.delete(content_file)

        binpkg = content_file.binpkg
        build = binpkg.build
        with self.assertRaises(RecordNotFound):
            files.get(build.machine, build.build_id, binpkg.cpvb, content_file.path)

    def test_delete_not_found(self, fixtures: Fixtures) -> None:
        content_file = fixtures.content_file
        files = fixtures.files

        with self.assertRaises(RecordNotFound):
            files.delete(content_file)

    def test_deindex_build(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        files.deindex_build(machine="polaris", build_id="26")

        self.assertEqual(files.count("polaris", "26", None), 0)
        self.assertEqual(files.count(None, None, None), 3)

    def test_count(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        self.assertEqual(files.count("lighthouse", "34", None), 2)
        self.assertEqual(
            files.count("lighthouse", "34", "app-shells/bash-5.2_p37-1"), 2
        )
        self.assertEqual(files.count("lighthouse", "34", "bogus-cat/bogus-pkg-1"), 0)

        self.assertEqual(files.count("polaris", "26", None), 3)
        self.assertEqual(files.count("polaris", "27", None), 1)
        self.assertEqual(files.count("polaris", None, None), 4)

        self.assertEqual(files.count("babette", "226", None), 0)

    def test_count_all(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        self.assertEqual(files.count(None, None, None), 6)

    def test_count_cpv_without_build_id(self, fixtures: Fixtures) -> None:
        files = fixtures.files

        with self.assertRaises(ValueError):
            files.count("lighthouse", None, "app-shells/bash-5.2_p37")

    def test_for_package(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkgs = files.for_package("lighthouse", "34", "app-shells/bash-5.2_p37-1")
        paths = {pkg.path for pkg in pkgs}
        self.assertEqual(paths, {Path("/bin/bash"), Path("/etc/skel")})

        pkgs = files.for_package("polaris", "26", "app-shells/bash-5.2_p37-1")
        paths = {pkg.path for pkg in pkgs}
        self.assertEqual(paths, {Path("/bin/bash")})

        pkgs = files.for_package("babette", "226", "app-shells/bash-5.2_p37-1")
        paths = {pkg.path for pkg in pkgs}
        self.assertEqual(paths, set())

    def test_for_build(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkgs = files.for_build("lighthouse", "34")
        total = len(list(pkgs))
        self.assertEqual(total, 2)

        pkgs = files.for_build("polaris", "26")
        total = len(list(pkgs))
        self.assertEqual(total, 3)

        pkgs = files.for_build("polaris", "27")
        total = len(list(pkgs))
        self.assertEqual(total, 1)

        pkgs = files.for_build("babette", "226")
        total = len(list(pkgs))
        self.assertEqual(total, 0)

    def test_for_machine(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkgs = files.for_machine("lighthouse")

        total = len(list(pkgs))
        self.assertEqual(total, 2)

        pkgs = files.for_machine("polaris")

        total = len(list(pkgs))
        self.assertEqual(total, 4)

    def test_search_full_path(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkg_files = list(files.search("/bin/bash"))
        self.assertEqual(len(pkg_files), 4)

        pkg_files = list(files.search("bin/bash"))
        self.assertEqual(len(pkg_files), 4)

    def test_search_basename(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkg_files = list(files.search("bash"))
        self.assertEqual(len(pkg_files), 4)

    def test_search_wildcard(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkg_files = list(files.search("sk*"))
        self.assertEqual(len(pkg_files), 1)

        pkg_files = list(files.search("*"))
        self.assertEqual(len(pkg_files), 6)

        pkg_files = list(files.search("*a*"))
        self.assertEqual(len(pkg_files), 5)

        pkg_files = list(files.search("z*"))
        self.assertEqual(len(pkg_files), 0)

        pkg_files = list(files.search("*ash"))
        self.assertEqual(len(pkg_files), 4)

    def test_search_with_empty_string(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkg_files = list(files.search(""))
        self.assertEqual(len(pkg_files), 0)

    def test_search_machines(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        pkg_files = list(files.search("bash", machines=["polaris"]))
        self.assertEqual(len(pkg_files), 3)

    def test_exists_false(self, fixtures: Fixtures) -> None:
        files = fixtures.files

        exists = files.exists(
            "lighthouse", "34", "app-shells/bash-5.2_p37", "/dev/null"
        )

        self.assertIs(exists, False)

    def test_exists_true(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        files.bulk_save(fixtures.bulk_content_files)

        exists = files.exists(
            "lighthouse", "34", "app-shells/bash-5.2_p37-1", "/bin/bash"
        )

        self.assertIs(exists, True)

    def test_save_with_override(self, fixtures: Fixtures) -> None:
        files = fixtures.files
        content_file = fixtures.content_file

        files.save(content_file)
        content_file = files.save(content_file, path="/dev/null")

        self.assertEqual("/dev/null", content_file.path)


class ContentFilesBackendTests(TestCase):
    def test_gets_given_backend(self) -> None:
        memory = import_module("gbp_fl.records.memory")

        backend = files_backend("memory")
        self.assertIsInstance(backend, memory.ContentFiles)

    def test_when_backend_not_found(self) -> None:
        with self.assertRaises(LookupError):
            files_backend("bogus")


class RepoFromSettingsTests(TestCase):
    def test(self) -> None:
        settings = Settings(RECORDS_BACKEND="django")
        repo = Repo.from_settings(settings)

        self.assertIsInstance(repo.files, django_orm.ContentFiles)
