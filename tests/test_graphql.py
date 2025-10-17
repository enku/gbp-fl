"""Tests for the GraphQL interface for gbp-fl"""

# pylint: disable=missing-docstring

from unittest import TestCase

import gbp_testkit.fixtures as testkit
from gbp_testkit.factories import BuildRecordFactory
from gbp_testkit.helpers import graphql
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, where

from gbp_fl.gateway import gateway

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

        del gateway.cache.stats
        gateway.cache.stats = stats

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


@given(lib.repo, testkit.publisher, testkit.client)
@given(build=lambda _: BuildRecordFactory(machine="babette", build_id="26"))
@given(lib.bulk_content_files)
@where(
    bulk_content_files="""
babette 26 acct-group/sgx-0-1            /usr/lib/sysusers.d/acct-group-sgx.conf _ 10
babette 26 app-admin/perl-cleaner-2.30-1 /usr/sbin/perl-cleaner                  _ 20274
babette 26 app-admin/perl-cleaner-2.30-1 /usr/share/man/man1/perl-cleaner.1      _ 1929
babette 26 app-arch/unzip-6.0_p26-1      /usr/bin/unzip                          _ 165896
babette 26 app-arch/unzip-6.0_p26-1      /usr/share/man/man1/unzip.1             _ 49640
babette 26 app-crypt/gpgme-1.14.0-1      /usr/bin/gpgme-json                     _ 88224
babette 26 app-crypt/gpgme-1.14.0-1      /usr/lib64/libgpgme.so                  _ 18
babette 26 app-crypt/gpgme-1.14.0-1      /usr/share/man/man1/gpgme-json.1        _ 1575
"""
)
class PackageFilesTests(TestCase):
    query = """query ($id: ID!) {
      build(id: $id) {
        id
        packageDetail {
          cpv
          files { path size }
        }
      }
    }"""

    def test(self, fixtures: Fixtures) -> None:
        repo = fixtures.repo
        build = fixtures.build

        publisher.pull(build)
        repo.files.bulk_save(fixtures.bulk_content_files)

        result = graphql(fixtures.client, self.query, {"id": "babette.26"})
        expected = {
            "id": "babette.26",
            "packageDetail": [
                {
                    "cpv": "acct-group/sgx-0",
                    "files": [
                        {"path": "/usr/lib/sysusers.d/acct-group-sgx.conf", "size": 10}
                    ],
                },
                {
                    "cpv": "app-admin/perl-cleaner-2.30",
                    "files": [
                        {"path": "/usr/sbin/perl-cleaner", "size": 20274},
                        {"path": "/usr/share/man/man1/perl-cleaner.1", "size": 1929},
                    ],
                },
                {
                    "cpv": "app-arch/unzip-6.0_p26",
                    "files": [
                        {"path": "/usr/bin/unzip", "size": 165896},
                        {"path": "/usr/share/man/man1/unzip.1", "size": 49640},
                    ],
                },
                {
                    "cpv": "app-crypt/gpgme-1.14.0",
                    "files": [
                        {"path": "/usr/bin/gpgme-json", "size": 88224},
                        {"path": "/usr/lib64/libgpgme.so", "size": 18},
                        {"path": "/usr/share/man/man1/gpgme-json.1", "size": 1575},
                    ],
                },
            ],
        }
        self.assertEqual(expected, result["data"]["build"])
