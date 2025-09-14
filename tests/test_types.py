"""Tests for gbp_fl.types"""

# pylint: disable=missing-docstring
from unittest import TestCase

from unittest_fixtures import Fixtures, given, where

from gbp_fl.records import ContentFiles
from gbp_fl.types import FileStats, MachineStats, Package

from . import lib


@given(lib.now, lib.binpkg)
@where(binpkg__cpvb="x11-apps/xhost-1.0.10-3")
class BinPkgTests(TestCase):
    def test_cpv(self, fixtures: Fixtures) -> None:
        self.assertEqual(fixtures.binpkg.cpv, "x11-apps/xhost-1.0.10")

    def test_build_id(self, fixtures: Fixtures) -> None:
        self.assertEqual(fixtures.binpkg.build_id, 3)


class PackageTests(TestCase):
    def test_cpvb(self) -> None:
        p = Package(
            cpv="x11-apps/xhost-1.0.10",
            build_id=3,
            repo="gentoo",
            build_time=0,
            path="x11-apps/xhost/xhost-1.0.10-3.gpkg.tar",
        )

        self.assertEqual("x11-apps/xhost-1.0.10-3", p.cpvb)


@given(lib.bulk_content_files, lib.repo)
class FileStatsTests(TestCase):
    def test_collect(self, fixtures: Fixtures) -> None:
        content_files = fixtures.bulk_content_files
        machine_counts = {"polaris": 4, "lighthouse": 1}
        files: ContentFiles = fixtures.repo.files
        files.bulk_save(content_files)

        file_stats = FileStats.collect(files, machine_counts)

        expected = FileStats(
            total=6,
            by_machine={
                "polaris": MachineStats(total=4, build_count=4),
                "lighthouse": MachineStats(total=2, build_count=1),
            },
        )
        self.assertEqual(file_stats, expected, file_stats)


class MachineStatsTests(TestCase):
    def test_init(self) -> None:
        ms = MachineStats(total=12, build_count=3)

        self.assertEqual(ms.total, 12)
        self.assertEqual(ms.build_count, 3)
        self.assertEqual(ms.per_build, 4)

    def test_build_count_zero(self) -> None:
        ms = MachineStats(total=0, build_count=0)

        self.assertEqual(ms.per_build, 0)

    def test_build_count_zero_but_has_files(self) -> None:
        with self.assertRaises(ValueError):
            MachineStats(total=12, build_count=0)
