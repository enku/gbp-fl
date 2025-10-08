"""Tests for the GraphQL interface for gbp-fl"""

# pylint: disable=missing-docstring

from dataclasses import replace
from unittest import TestCase
from unittest.mock import Mock

import gbp_testkit.fixtures as testkit
from gbp_testkit.helpers import graphql
from gentoo_build_publisher import publisher
from gentoo_build_publisher.cache import cache
from gentoo_build_publisher.graphql import schema
from gentoo_build_publisher.records import BuildRecord
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given

from gbp_fl.types import STATS_CACHE_KEY, BinPkg, Build

from . import lib


@given(lib.repo, lib.bulk_content_files, testkit.client)
class FileListSearchTests(TestCase):
    def test_search_without_machine(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)

        query = """
          query filesStartingWithBa {
            flSearch(key: "ba*") { path binpkg { cpvb } }
          }
        """
        result = graphql(fixtures.client, query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 4)

    def test_search_without_machine_no_match(self, fixtures: Fixtures) -> None:
        query = 'query { flSearch(key: "python") { path binpkg { cpvb } } }'

        result = graphql(fixtures.client, query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 0)

    def test_search_with_machine(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)
        query = """
          query {
            flSearch(key: "ba*", machine: "polaris") {
              path binpkg { cpvb repo url }
            }
          }
        """
        result = graphql(fixtures.client, query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 3)


@given(lib.repo, lib.bulk_content_files, testkit.client)
class ResolveQueryCountTests(TestCase):
    query = "query totalFileCount { flCount }"

    query_with_machine = """
      query totalFileCountMachine($machine: String!) {
        flCount(machine: $machine)
      }
    """
    query_with_build = """
      query totalFileCountMachine($machine: String!, $buildId: String!) {
        flCount(machine: $machine, buildId: $buildId)
      }
    """

    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(fixtures.client, self.query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 6)

    def test_with_no_content_files(self, fixtures: Fixtures) -> None:
        result = graphql(fixtures.client, self.query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 0)

    def test_with_machine(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(
            fixtures.client, self.query_with_machine, {"machine": "lighthouse"}
        )

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 2)

    def test_with_build(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(
            fixtures.client,
            self.query_with_build,
            {"machine": "polaris", "buildId": "26"},
        )

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 3)


@given(testkit.publisher, lib.now, record=testkit.build_record)
class ResolveBinPkgBuildTests(TestCase):

    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        build_record: BuildRecord = replace(f.record, submitted=f.now)
        build = Build(machine=build_record.machine, build_id=build_record.build_id)
        binpkg = BinPkg(
            build=build,
            cpvb="dev-language/python-3.13.1-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        publisher.repo.build_records.save(build_record)
        result = schema.type_map["flBinPkg"].fields["build"].resolve(binpkg, Mock())

        self.assertEqual(result, build_record)


@given(lib.repo, lib.bulk_content_files, testkit.client)
class FileListListTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)

        query = """
          query {
            flList(machine: "lighthouse", buildId: "34", cpvb: "app-shells/bash-5.2_p37-1") {
              path timestamp size
            }
          }
        """
        result = graphql(fixtures.client, query)

        self.assertTrue("errors" not in result, result.get("errors"))
        expected = [
            {
                "path": "/bin/bash",
                "size": 850648,
                "timestamp": "2025-01-26T12:57:37+00:00",
            },
            {
                "path": "/etc/skel",
                "size": 850648,
                "timestamp": "2025-01-26T12:57:37+00:00",
            },
        ]
        self.assertEqual(expected, result["data"]["flList"])


@given(lib.repo, testkit.client, testkit.publisher)
class FlListPackages(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        build = GBPBuild(machine="lighthouse", build_id="34404")
        publisher.publish(build)

        query = """
          query {
            flListPackages(machine: "lighthouse", buildId: "34404") {
              cpvb
              files {
                path timestamp size
              }
            }
          }
        """
        result = graphql(fixtures.client, query)

        self.assertTrue("errors" not in result, result.get("errors"))

        # the files array will be empty since the artifact builder factory doesn't know
        # how to create actual package files.
        expected = [
            {"cpvb": "acct-group/sgx-0-1", "files": []},
            {"cpvb": "app-admin/perl-cleaner-2.30-1", "files": []},
            {"cpvb": "app-arch/unzip-6.0_p26-1", "files": []},
            {"cpvb": "app-crypt/gpgme-1.14.0-1", "files": []},
        ]
        self.assertEqual(expected, result["data"]["flListPackages"])


@given(lib.stats, testkit.client, testkit.publisher)
class MachineSummaryStatsTests(TestCase):
    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        stats = f.stats
        mstats = stats.by_machine

        for machine in mstats:
            publisher.pull(GBPBuild(machine=machine, build_id="test"))

        cache.clear()
        cache.set(STATS_CACHE_KEY, stats)

        query = """
          query {
            machines {
              machine
              fileStats {
                total
                perBuild
              }
            }
        }
        """
        result = graphql(f.client, query)

        expected = [
            {
                "machine": "lighthouse",
                "fileStats": {
                    "perBuild": mstats["lighthouse"].per_build,
                    "total": mstats["lighthouse"].total,
                },
            },
            {
                "machine": "polaris",
                "fileStats": {
                    "perBuild": mstats["polaris"].per_build,
                    "total": mstats["polaris"].total,
                },
            },
        ]
        self.assertEqual(expected, result["data"]["machines"])
