"""Handler for `gbp fl fetch`"""

import argparse
import re
from dataclasses import dataclass

import requests
from gbpcli.gbp import GBP
from gbpcli.types import Console
from yarl import URL

# lighthouse/32284/www-client/firefox-135.0-1::gentoo
PKGSPEC_RE_STR = r"""
(?P<machine>[a-z]\w*)/
(?P<build_id>[0-9]+)/
(?P<c>[a-z0-9]+-[a-z0-9]+)/
(?P<p>[a-z].*)-(?P<v>[0-9].*)-(?P<b>[0-9]*)::
(?P<repo>[a-z]+)
"""

BUFSIZE = 1024
PKGSPEC_RE = re.compile(PKGSPEC_RE_STR, re.I | re.X)


@dataclass
class Parsed:
    """Parsed package spec"""

    machine: str
    build_id: str
    c: str
    p: str
    v: str
    b: int
    repo: str


def handler(args: argparse.Namespace, gbp: GBP, console: Console) -> int:
    """Get package files from Gentoo Build Publisher"""
    if (spec := parse_pkgspec(args.pkgspec)) is None:
        console.err.print(f"[red]Invalid specifier: {args.pkgspec}[/red]")
        return 1

    path = (
        f"machines/{spec.machine}/builds/{spec.build_id}/packages/{spec.c}"
        f"/{spec.p}/{spec.p}-{spec.v}-{spec.b}"
    )
    url = URL(gbp.query._url).origin() / path  # pylint: disable=protected-access

    with requests.get(str(url), stream=True, timeout=300) as response:
        if response.status_code == 404:
            console.err.print("[red]The requested package was not found.[/red]")
            return 2

        output = URL(response.url).name

        with open(output, "wb", buffering=BUFSIZE) as fp:
            for chunk in response.iter_content(BUFSIZE):
                fp.write(chunk)
        console.out.print(f"package saved as {output}")

    return 0


HELP = handler.__doc__


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Build command-line arguments"""
    parser.add_argument("pkgspec")


def parse_pkgspec(pkgspec: str) -> Parsed | None:
    """Parse the given spec"""
    if match := PKGSPEC_RE.match(pkgspec):
        parsed = Parsed(**match.groupdict())  # type: ignore
        parsed.b = int(parsed.b)
        return parsed
    return None
