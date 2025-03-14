"""The gbp fl ls subcommand"""

import argparse
import datetime as dt
from typing import TypedDict

from gbpcli import render
from gbpcli.gbp import GBP
from gbpcli.types import Console
from rich import box
from rich.table import Table

from gbp_fl import utils

from . import resolve_build_id

HELP = "List files in a package"


class ContentFileDict(TypedDict):
    """ContentFiles dict returned from queries"""

    path: str
    size: int
    timestamp: str


def handler(args: argparse.Namespace, gbp: GBP, console: Console) -> int:
    """List files in a package"""
    if (spec := utils.parse_pkgspec(args.pkgspec)) is None:
        console.err.print(f"[red]Invalid specifier: {args.pkgspec}[/red]")
        return 1

    build_id = resolve_build_id(spec.machine, spec.build_id, gbp) or ""
    response, _ = gbp.query.gbp_fl.list(  # type: ignore
        machine=spec.machine, buildId=build_id, cpvb=spec.cpvb, extended=args.long
    )
    fl_list: list[ContentFileDict] = response["flList"]
    fl_list.sort(key=lambda item: item["path"])

    (print_long if args.long else print_short)(fl_list, console)

    return 0


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Build command-line arguments"""
    parser.add_argument(
        "-l", "--long", action="store_true", default=False, help="Print in long format"
    )
    parser.add_argument("pkgspec")


def print_short(cfs: list[ContentFileDict], console: Console) -> None:
    """Print ContentFiles in short format"""
    for item in cfs:
        console.out.print(item["path"])


def print_long(cfs: list[ContentFileDict], console: Console) -> None:
    """Print ContentFiles in long format"""
    table = create_table()
    for item in cfs:
        table.add_row(*format_row(item))

    console.out.print(table)


def create_table() -> Table:
    """Create and return a Table for displaying files in long format"""
    table = Table(box=box.ROUNDED, style="box")
    table.add_column("Size", justify="right", header_style="header")
    table.add_column("Timestamp", header_style="header")
    table.add_column("Path", header_style="header")

    return table


def format_row(item: ContentFileDict) -> tuple[str, str, str]:
    """Format the item for adding to a table"""
    timestamp = render.format_timestamp(
        dt.datetime.fromisoformat(item["timestamp"]).astimezone(render.LOCAL_TIMEZONE)
    )
    return (
        f"[filesize]{item['size']}[/filesize]",
        f"[timestamp]{timestamp}[/timestamp]",
        f"[tag]{item['path']}[/tag]",
    )
