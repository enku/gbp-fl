# pylint: disable=missing-docstring
import datetime as dt
from argparse import ArgumentParser, Namespace
from dataclasses import replace
from unittest.mock import Mock, patch

from unittest_fixtures import TestCase, requires

from gbp_fl.cli import search

from .utils import LOCAL_TIMEZONE

DAY = dt.timedelta(days=1, minutes=11, seconds=12)


@requires("gbp_client", "repo", "bulk_content_files", "console")
@patch("gbp_fl.graphql.GBPGateway")
@patch("gbpcli.render.LOCAL_TIMEZONE", new=LOCAL_TIMEZONE)
class SearchTests(TestCase):
    def test(self, gpbgateway: Mock) -> None:
        cfs = self.fixtures.bulk_content_files
        repo = self.fixtures.repo
        now = self.fixtures.now

        for cf in cfs:
            cf = replace(cf, timestamp=now)
            repo.files.save(cf)
            now = now + DAY

        bash_file_indexes = [0, 3, 4, 5]

        gpbgateway.return_value.get_build_record.side_effect = tuple(
            Mock(
                machine=cfs[i].binpkg.build.machine,
                build_id=cfs[i].binpkg.build.build_id,
                id=cfs[i].binpkg.build.build_id,
            )
            for i in bash_file_indexes
        )
        args = Namespace(key="bash", machine=None)
        gbp = self.fixtures.gbp_client
        console = self.fixtures.console

        console.out.print("$ gbp fl search bash")
        status = search.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual(
            TEST1_SEARCH_OUTPUT,
            console.out.file.getvalue(),
            "\n" + console.out.file.getvalue(),
        )

    def test_with_missing_metadata(self, gpbgateway: Mock) -> None:
        # When a package is being deleted, e.g. during a purge run, the binpkg metadata
        # may be gone. This results in an error in the graphql call and the binpkg field
        # being set to null. We want to (silently) ignore those
        cfs = self.fixtures.bulk_content_files
        repo = self.fixtures.repo
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
        gpbgateway.return_value.get_build_record.side_effect = tuple(build_records)

        args = Namespace(key="bash", machine=None)
        gbp = self.fixtures.gbp_client
        console = self.fixtures.console

        console.out.print("$ gbp fl search bash")
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
