"""Tests for the GraphQL interface for gbp-fl"""

from dataclasses import replace
from typing import Any
from unittest.mock import Mock, patch

from django.test.client import Client
from gentoo_build_publisher.records import BuildRecord
from unittest_fixtures import (
    FixtureContext,
    FixtureOptions,
    Fixtures,
    TestCase,
    depends,
    requires,
)

import gbp_fl.graphql.binpkg
from gbp_fl.records import Repo
from gbp_fl.types import BinPkg, Build

# pylint: disable=missing-docstring


@depends("settings")
def repo_fixture(_options: FixtureOptions, fixtures: Fixtures) -> FixtureContext[Repo]:
    repo: Repo = Repo.from_settings(fixtures.settings)

    with patch("gbp_fl.graphql.queries.Repo.from_settings", return_value=repo):
        yield repo


@requires(repo_fixture, "bulk_content_files")
class FileListSearchTests(TestCase):
    def test_search_without_machine(self) -> None:
        f = self.fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)

        query = """
          query filesStartingWithBa {
            flSearch(key: "ba*") { path binpkg { cpvb } }
          }
        """
        result = graphql(query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 4)

    def test_search_without_machine_no_match(self) -> None:
        query = 'query { flSearch(key: "python") { path binpkg { cpvb } } }'

        result = graphql(query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 0)

    def test_search_with_machine(self) -> None:
        f = self.fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)
        query = """
          query {
            flSearch(key: "ba*", machine: "polaris") {
              path binpkg { cpvb repo url }
            }
          }
        """
        result = graphql(query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(len(result["data"]["flSearch"]), 3)


@requires(repo_fixture, "bulk_content_files")
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

    def test(self) -> None:
        f = self.fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(self.query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 6)

    def test_with_no_content_files(self) -> None:
        result = graphql(self.query)

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 0)

    def test_with_machine(self) -> None:
        f = self.fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(self.query_with_machine, machine="lighthouse")

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 2)

    def test_with_build(self) -> None:
        f = self.fixtures
        repo = f.repo

        repo.files.bulk_save(f.bulk_content_files)
        result = graphql(self.query_with_build, machine="polaris", buildId="26")

        self.assertTrue("errors" not in result, result.get("errors"))
        self.assertEqual(result["data"]["flCount"], 3)


@requires(repo_fixture, "publisher", "build_record", "bulk_content_files")
class ResolveBinPkgBuildTests(TestCase):
    def test(self) -> None:
        f = self.fixtures
        publisher = f.publisher
        build_record: BuildRecord = replace(f.build_record, submitted=f.now)
        build = Build(machine=build_record.machine, build_id=build_record.build_id)
        binpkg = BinPkg(
            build=build,
            cpvb="dev-language/python-3.13.1-3",
            repo="gentoo",
            build_time=self.fixtures.now,
        )
        publisher.repo.build_records.save(build_record)
        result = gbp_fl.graphql.binpkg.build(binpkg, Mock())

        self.assertEqual(result, build_record)


@requires(repo_fixture, "bulk_content_files")
class FileListListTests(TestCase):
    def test(self) -> None:
        f = self.fixtures
        repo = f.repo
        repo.files.bulk_save(f.bulk_content_files)

        query = """
          query {
            flList(machine: "lighthouse", buildId: "34", cpvb: "app-shells/bash-5.2_p37-1") {
              path timestamp size
            }
          }
        """
        result = graphql(query)

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


def graphql(query: str, **variables: Any) -> Any:
    """Execute GraphQL query on the Django test client

    Return parse JSON response
    """
    post_data = {"query": query, "variables": variables or None}
    client = Client(raise_request_exception=True)
    response = client.post("/graphql", post_data, content_type="application/json")

    return response.json()
