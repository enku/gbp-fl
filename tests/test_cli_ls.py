# pylint: disable=missing-docstring,unused-argument
from unittest import TestCase

import gbp_testkit.fixtures as testkit
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild
from unittest_fixtures import Fixtures, given, where

from gbp_fl.cli import ls

from . import lib

BULK_CONTENT_FILES = """
lighthouse 34 app-arch/tar-1.35-1 /usr/share/info/tar.info-2        gentoo  317618 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/info/tar.info-3        gentoo   49627 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/man/man1/gtar.1        gentoo   42162 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/man/man8/grmt.8        gentoo    5361 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/README    gentoo    9756 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/ChangeLog gentoo  579457 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/AUTHORS   gentoo     601 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/info/tar.info          gentoo   13479 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/info/tar.info-1        gentoo  304308 2025-02-08T07:34:00
lighthouse 34 app-arch/tar-1.35-1 /usr/share/man/man8/rmt.8         gentoo       0 2025-02-08T07:34:01
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/NEWS      gentoo   67627 2025-02-08T07:34:01
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/THANKS    gentoo   20500 2025-02-08T07:34:01
lighthouse 34 app-arch/tar-1.35-1 /usr/share/doc/tar-1.35/TODO      gentoo    2151 2025-02-08T07:34:01
lighthouse 34 app-arch/tar-1.35-1 /bin/gtar                         gentoo  411312 2025-02-08T07:34:01
polaris    26 app-arch/tar-1.35-1       /bin/gtar
polaris    26 app-shells/bash-5.2_p37-1 /bin/bash
polaris    26 app-shells/bash-5.2_p37-2 /bin/bash
polaris    27 app-shells/bash-5.2_p37-1 /bin/bash
"""


@given(
    lib.local_timezone,
    lib.bulk_content_files,
    testkit.console,
    lib.gbp_client,
    lib.repo,
    testkit.publisher,
)
@where(
    records_db={"records_backend": "memory"},
    bulk_content_files=BULK_CONTENT_FILES,
    repo="gbp_fl.graphql.queries.repo",
)
class LsTests(TestCase):

    def test_short_format(self, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        repo.files.bulk_save(cfs)

        pkgspec = "lighthouse/34/app-arch/tar-1.35-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = lib.parse_args(cmd)
        console = fixtures.console
        gbp = fixtures.gbp_client

        lib.print_command(cmd, console)
        status = ls.handler(args, gbp, console)

        self.assertEqual(0, status)
        self.assertEqual(LS_OUTPUT, console.out.file.getvalue())

    def test_long_format(self, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        repo.files.bulk_save(cfs)

        pkgspec = "lighthouse/34/app-arch/tar-1.35-1"
        cmd = f"gbp fl ls -l {pkgspec}"
        args = lib.parse_args(cmd)
        console = fixtures.console
        gbp = fixtures.gbp_client

        lib.print_command(cmd, console)
        status = ls.handler(args, gbp, console)

        self.assertEqual(0, status)
        self.assertEqual(LS_LONG_OUTPUT, console.out.file.getvalue())

    def test_with_tag(self, fixtures: Fixtures) -> None:
        cfs = fixtures.bulk_content_files
        repo = fixtures.repo
        repo.files.bulk_save(cfs)

        publisher.publish(GBPBuild(machine="lighthouse", build_id="34"))
        pkgspec = "lighthouse/@/app-arch/tar-1.35-1"
        cmd = f"gbp fl ls -l {pkgspec}"
        args = lib.parse_args(cmd)
        console = fixtures.console
        gbp = fixtures.gbp_client

        lib.print_command(cmd, console)
        status = ls.handler(args, gbp, console)

        self.assertEqual(0, status)
        expected = LS_LONG_OUTPUT.replace("lighthouse/34/", "lighthouse/@/")
        self.assertEqual(expected, console.out.file.getvalue())

    def test_invalid_spec(self, fixtures: Fixtures) -> None:
        pkgspec = "lighthouse/34/bash-5.2_p37-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = lib.parse_args(cmd)
        gbp = fixtures.gbp_client
        console = fixtures.console

        status = ls.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(f"Invalid specifier: {pkgspec}\n", console.err.file.getvalue())
        self.assertEqual("", console.out.file.getvalue())

    def test_package_doesnt_exist(self, fixtures: Fixtures) -> None:
        pkgspec = "lighthouse/34/sys-apps/bogus-0.0-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = lib.parse_args(cmd)
        gbp = fixtures.gbp_client
        console = fixtures.console

        status = ls.handler(args, gbp, console)

        self.assertEqual(status, 0)
        self.assertEqual("", console.out.file.getvalue())


LS_OUTPUT = """$ gbp fl ls lighthouse/34/app-arch/tar-1.35-1
/bin/gtar
/usr/share/doc/tar-1.35/AUTHORS
/usr/share/doc/tar-1.35/ChangeLog
/usr/share/doc/tar-1.35/NEWS
/usr/share/doc/tar-1.35/README
/usr/share/doc/tar-1.35/THANKS
/usr/share/doc/tar-1.35/TODO
/usr/share/info/tar.info
/usr/share/info/tar.info-1
/usr/share/info/tar.info-2
/usr/share/info/tar.info-3
/usr/share/man/man1/gtar.1
/usr/share/man/man8/grmt.8
/usr/share/man/man8/rmt.8
"""
LS_LONG_OUTPUT = """$ gbp fl ls -l lighthouse/34/app-arch/tar-1.35-1
╭────────┬───────────────────┬───────────────────────────────────╮
│   Size │ Timestamp         │ Path                              │
├────────┼───────────────────┼───────────────────────────────────┤
│ 411312 │ 02/08/25 06:34:01 │ /bin/gtar                         │
│    601 │ 02/08/25 06:34:00 │ /usr/share/doc/tar-1.35/AUTHORS   │
│ 579457 │ 02/08/25 06:34:00 │ /usr/share/doc/tar-1.35/ChangeLog │
│  67627 │ 02/08/25 06:34:01 │ /usr/share/doc/tar-1.35/NEWS      │
│   9756 │ 02/08/25 06:34:00 │ /usr/share/doc/tar-1.35/README    │
│  20500 │ 02/08/25 06:34:01 │ /usr/share/doc/tar-1.35/THANKS    │
│   2151 │ 02/08/25 06:34:01 │ /usr/share/doc/tar-1.35/TODO      │
│  13479 │ 02/08/25 06:34:00 │ /usr/share/info/tar.info          │
│ 304308 │ 02/08/25 06:34:00 │ /usr/share/info/tar.info-1        │
│ 317618 │ 02/08/25 06:34:00 │ /usr/share/info/tar.info-2        │
│  49627 │ 02/08/25 06:34:00 │ /usr/share/info/tar.info-3        │
│  42162 │ 02/08/25 06:34:00 │ /usr/share/man/man1/gtar.1        │
│   5361 │ 02/08/25 06:34:00 │ /usr/share/man/man8/grmt.8        │
│      0 │ 02/08/25 06:34:01 │ /usr/share/man/man8/rmt.8         │
╰────────┴───────────────────┴───────────────────────────────────╯
"""
