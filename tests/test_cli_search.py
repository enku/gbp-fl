# pylint: disable=missing-docstring,unused-argument
import datetime as dt
from argparse import ArgumentParser
from dataclasses import replace
from unittest import TestCase
from unittest.mock import Mock, patch

import gbp_testkit.fixtures as testkit
from gbp_testkit.helpers import parse_args, print_command
from unittest_fixtures import Fixtures, given, where

from gbp_fl.cli import search
from gbp_fl.types import ContentFile

from . import fixtures as tf
from .utils import LOCAL_TIMEZONE

DAY = dt.timedelta(days=1, minutes=11, seconds=12)


@given(tf.environ, tf.gbp_client, tf.repo, tf.bulk_content_files, testkit.console)
@where(repo="gbp_fl.graphql.queries.repo", environ={"GBPCLI_MYMACHINES": "lighthouse"})
@patch("gbp_fl.graphql.binpkg.gateway")
@patch("gbpcli.render.LOCAL_TIMEZONE", new=LOCAL_TIMEZONE)
class SearchTests(TestCase):
    options = {"records_backend": "memory"}

    def test(self, gateway: Mock, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        now = fixtures.now

        for cf in cfs:
            cf = replace(cf, timestamp=now)
            repo.files.save(cf)
            now = now + DAY

        bash_file_indexes = [0, 3, 4, 5]

        make_build_records(gateway, [cfs[i] for i in bash_file_indexes])

        cmdline = "gbp fl search bash"
        args = parse_args(cmdline)
        gbp = fixtures.gbp_client
        console = fixtures.console

        print_command(cmdline, console)
        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual(
            TEST1_SEARCH_OUTPUT,
            console.out.file.getvalue(),
            "\n" + console.out.file.getvalue(),
        )

    def test_with_machine(self, gateway: Mock, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        now = fixtures.now

        for cf in cfs:
            cf = replace(cf, timestamp=now)
            repo.files.save(cf)
            now = now + DAY

        bash_file_indexes = [0, 3, 4, 5]

        make_build_records(gateway, [cfs[i] for i in bash_file_indexes])

        cmdline = "gbp fl search -m lighthouse bash"
        args = parse_args(cmdline)
        gbp = fixtures.gbp_client
        console = fixtures.console

        print_command(cmdline, console)
        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual(
            TEST3_SEARCH_OUTPUT,
            console.out.file.getvalue(),
            "\n" + console.out.file.getvalue(),
        )

    def test_with_mine(self, gateway: Mock, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        now = fixtures.now

        for cf in cfs:
            cf = replace(cf, timestamp=now)
            repo.files.save(cf)
            now = now + DAY

        bash_file_indexes = [0, 3, 4, 5]

        make_build_records(gateway, [cfs[i] for i in bash_file_indexes])

        cmdline = "gbp fl search --mine bash"
        args = parse_args(cmdline)
        gbp = fixtures.gbp_client
        console = fixtures.console

        print_command(cmdline, console)
        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual(
            TEST4_SEARCH_OUTPUT,
            console.out.file.getvalue(),
            "\n" + console.out.file.getvalue(),
        )

    def test_no_match(self, gateway: Mock, fixtures: Fixtures) -> None:
        cmdline = "gbp fl search bash"
        args = parse_args(cmdline)
        gbp = fixtures.gbp_client
        console = fixtures.console

        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual("", console.out.file.getvalue())

    def test_with_missing_metadata(self, gateway: Mock, fixtures: Fixtures) -> None:
        # When a package is being deleted, e.g. during a purge run, the binpkg metadata
        # may be gone. This results in an error in the graphql call and the binpkg field
        # being set to null. We want to (silently) ignore those
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        repo.files.bulk_save(cfs)

        bash_file_indexes = [0, 3, 4, 5]
        build_records = [
            Mock(
                machine=cfs[i].binpkg.build.machine,
                build_id=cfs[i].binpkg.build.build_id,
                id=cfs[i].binpkg.build.build_id,
            )
            for i in bash_file_indexes
        ]
        # make the second one return None
        build_records[1] = None  # type: ignore
        gateway.get_build_record.side_effect = tuple(build_records)

        cmdline = "gbp fl search bash"
        args = parse_args(cmdline)
        gbp = fixtures.gbp_client
        console = fixtures.console

        print_command(cmdline, console)
        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual(
            TEST2_SEARCH_OUTPUT,
            console.out.file.getvalue(),
            "\n" + console.out.file.getvalue(),
        )


class ParseArgsTests(TestCase):
    def test(self) -> None:
        parser = ArgumentParser()
        search.parse_args(parser)


def make_build_records(gateway: Mock, content_files: list[ContentFile]) -> None:
    """Mock gateway to return content_file when .get_build_record() is called"""
    gateway.get_build_record.side_effect = tuple(
        Mock(
            machine=content_file.binpkg.build.machine,
            build_id=content_file.binpkg.build.build_id,
            id=content_file.binpkg.build.build_id,
        )
        for content_file in content_files
    )


TEST1_SEARCH_OUTPUT = """$ gbp fl search bash
╭────────┬───────────────────┬─────────────────────────────────────────┬───────────╮
│   Size │ Timestamp         │ Package                                 │ Path      │
├────────┼───────────────────┼─────────────────────────────────────────┼───────────┤
│ 850648 │ 01/26/25 05:57:37 │ lighthouse/34/app-shells/bash-5.2_p37-1 │ /bin/bash │
│ 850648 │ 01/29/25 06:31:13 │ polaris/26/app-shells/bash-5.2_p37-1    │ /bin/bash │
│ 850648 │ 01/30/25 06:42:25 │ polaris/26/app-shells/bash-5.2_p37-2    │ /bin/bash │
│ 850648 │ 01/31/25 06:53:37 │ polaris/27/app-shells/bash-5.2_p37-1    │ /bin/bash │
╰────────┴───────────────────┴─────────────────────────────────────────┴───────────╯
"""
TEST2_SEARCH_OUTPUT = """$ gbp fl search bash
╭────────┬───────────────────┬─────────────────────────────────────────┬───────────╮
│   Size │ Timestamp         │ Package                                 │ Path      │
├────────┼───────────────────┼─────────────────────────────────────────┼───────────┤
│ 850648 │ 01/26/25 05:57:37 │ lighthouse/34/app-shells/bash-5.2_p37-1 │ /bin/bash │
│ 850648 │ 01/26/25 05:57:37 │ polaris/26/app-shells/bash-5.2_p37-2    │ /bin/bash │
│ 850648 │ 01/26/25 05:57:37 │ polaris/27/app-shells/bash-5.2_p37-1    │ /bin/bash │
╰────────┴───────────────────┴─────────────────────────────────────────┴───────────╯
"""
TEST3_SEARCH_OUTPUT = """$ gbp fl search -m lighthouse bash
╭────────┬───────────────────┬─────────────────────────────────────────┬───────────╮
│   Size │ Timestamp         │ Package                                 │ Path      │
├────────┼───────────────────┼─────────────────────────────────────────┼───────────┤
│ 850648 │ 01/26/25 05:57:37 │ lighthouse/34/app-shells/bash-5.2_p37-1 │ /bin/bash │
╰────────┴───────────────────┴─────────────────────────────────────────┴───────────╯
"""
TEST4_SEARCH_OUTPUT = """$ gbp fl search --mine bash
╭────────┬───────────────────┬─────────────────────────────────────────┬───────────╮
│   Size │ Timestamp         │ Package                                 │ Path      │
├────────┼───────────────────┼─────────────────────────────────────────┼───────────┤
│ 850648 │ 01/26/25 05:57:37 │ lighthouse/34/app-shells/bash-5.2_p37-1 │ /bin/bash │
╰────────┴───────────────────┴─────────────────────────────────────────┴───────────╯
"""
