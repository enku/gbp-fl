"""Tests for the GraphQL interface for gbp-fl"""

from dataclasses import replace
from unittest import TestCase
from unittest.mock import Mock

from django.test import TestCase as DjangoTestCase
from gbp_testkit.helpers import graphql
from gentoo_build_publisher.records import BuildRecord
from unittest_fixtures import Fixtures, given, where

import gbp_fl.graphql.binpkg
from gbp_fl.types import BinPkg, Build

# pylint: disable=missing-docstring


@given("repo", "bulk_content_files", "client")
@where(records_backend="memory")
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


@given("repo", "bulk_content_files", "client")
@where(records_backend="memory")
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


# Any test that uses "record" depends on Django, because "records" depends on Django.
# This needs to be fixed
@where(records_db__backend="django")
@given("publisher", "record", "now")
class ResolveBinPkgBuildTests(DjangoTestCase):

    def test(self, fixtures: Fixtures) -> None:
        f = fixtures
        publisher = f.publisher
        build_record: BuildRecord = replace(f.record, submitted=f.now)
        build = Build(machine=build_record.machine, build_id=build_record.build_id)
        binpkg = BinPkg(
            build=build,
            cpvb="dev-language/python-3.13.1-3",
            repo="gentoo",
            build_time=fixtures.now,
        )
        publisher.repo.build_records.save(build_record)
        result = gbp_fl.graphql.binpkg.build(binpkg, Mock())

        self.assertEqual(result, build_record)


@given("repo", "bulk_content_files", "client")
@where(records_backend="memory")
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
