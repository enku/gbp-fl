"""Handler for `gbp fl fetch`"""

import argparse
from typing import Iterable

import requests
from gbpcli.gbp import GBP
from gbpcli.types import Console
from gbpcli.utils import resolve_build_id
from yarl import URL

from gbp_fl import utils

BUFSIZE = 1024
HELP = "Get package files from Gentoo Build Publisher"


def handler(args: argparse.Namespace, gbp: GBP, console: Console) -> int:
    """Get package files from Gentoo Build Publisher"""
    if (spec := utils.parse_pkgspec(args.pkgspec)) is None:
        console.err.print(f"[red]Invalid specifier: {args.pkgspec}[/red]")
        return 1

    build = resolve_build_id(spec.machine, spec.build_id, gbp)
    path = (
        f"machines/{spec.machine}/builds/{build.number}/packages/{spec.c}"
        f"/{spec.p}/{spec.p}-{spec.v}-{spec.b}"
    )
    url = URL(gbp.query._url).origin() / path  # pylint: disable=protected-access

    with requests.get(str(url), stream=True, timeout=300) as response:
        if response.status_code == 404:
            console.err.print("[red]The requested package was not found.[/red]")
            return 2

        output = URL(response.url).name

        save_chunks_to_file(response.iter_content(BUFSIZE), output)
        console.out.print(f"package saved as [package]{output}[/package]")

    return 0


def save_chunks_to_file(chunks: Iterable[bytes], filename: str) -> None:
    """Save the content to the given filename"""
    with open(filename, "wb", buffering=BUFSIZE) as fp:
        for chunk in chunks:
            fp.write(chunk)


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Build command-line arguments"""
    parser.add_argument("pkgspec")
