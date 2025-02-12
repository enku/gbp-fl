# pylint: disable=missing-docstring
import unittest_fixtures as uf

from gbp_fl.cli import ls

from .utils import parse_args, print_command


@uf.requires("bulk_content_files", "console", "gbp_client", "repo")
class LsTests(uf.TestCase):
    options = {
        "bulk_content_files": """
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
    }

    def test_short_format(self) -> None:
        cfs = self.fixtures.bulk_content_files
        repo = self.fixtures.repo
        repo.files.bulk_save(cfs)

        pkgspec = "lighthouse/34/app-arch/tar-1.35-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = parse_args(cmd)
        console = self.fixtures.console
        gbp = self.fixtures.gbp_client

        print_command(cmd, console)
        status = ls.handler(args, gbp, console)

        self.assertEqual(0, status)
        self.assertEqual(LS_OUTPUT, console.out.file.getvalue())

    def test_long_format(self) -> None:
        cfs = self.fixtures.bulk_content_files
        repo = self.fixtures.repo
        repo.files.bulk_save(cfs)

        pkgspec = "lighthouse/34/app-arch/tar-1.35-1"
        cmd = f"gbp fl ls -l {pkgspec}"
        args = parse_args(cmd)
        console = self.fixtures.console
        gbp = self.fixtures.gbp_client

        print_command(cmd, console)
        status = ls.handler(args, gbp, console)

        self.assertEqual(0, status)
        self.assertEqual(LS_LONG_OUTPUT, console.out.file.getvalue())

    def test_invalid_spec(self) -> None:
        pkgspec = "lighthouse/34/bash-5.2_p37-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = parse_args(cmd)
        gbp = self.fixtures.gbp_client
        console = self.fixtures.console

        status = ls.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(f"Invalid specifier: {pkgspec}\n", console.err.file.getvalue())
        self.assertEqual("", console.out.file.getvalue())

    def test_package_doesnt_exist(self) -> None:
        pkgspec = "lighthouse/34/sys-apps/bogus-0.0-1"
        cmd = f"gbp fl ls {pkgspec}"
        args = parse_args(cmd)
        gbp = self.fixtures.gbp_client
        console = self.fixtures.console

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
│ 411312 │ 02/08/25 07:34:01 │ /bin/gtar                         │
│    601 │ 02/08/25 07:34:00 │ /usr/share/doc/tar-1.35/AUTHORS   │
│ 579457 │ 02/08/25 07:34:00 │ /usr/share/doc/tar-1.35/ChangeLog │
│  67627 │ 02/08/25 07:34:01 │ /usr/share/doc/tar-1.35/NEWS      │
│   9756 │ 02/08/25 07:34:00 │ /usr/share/doc/tar-1.35/README    │
│  20500 │ 02/08/25 07:34:01 │ /usr/share/doc/tar-1.35/THANKS    │
│   2151 │ 02/08/25 07:34:01 │ /usr/share/doc/tar-1.35/TODO      │
│  13479 │ 02/08/25 07:34:00 │ /usr/share/info/tar.info          │
│ 304308 │ 02/08/25 07:34:00 │ /usr/share/info/tar.info-1        │
│ 317618 │ 02/08/25 07:34:00 │ /usr/share/info/tar.info-2        │
│  49627 │ 02/08/25 07:34:00 │ /usr/share/info/tar.info-3        │
│  42162 │ 02/08/25 07:34:00 │ /usr/share/man/man1/gtar.1        │
│   5361 │ 02/08/25 07:34:00 │ /usr/share/man/man8/grmt.8        │
│      0 │ 02/08/25 07:34:01 │ /usr/share/man/man8/rmt.8         │
╰────────┴───────────────────┴───────────────────────────────────╯
"""
