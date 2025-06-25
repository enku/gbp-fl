"""search subcommand for gbp-fl"""

import argparse
import datetime as dt
from types import SimpleNamespace
from typing import Any

from gbpcli import render, utils
from gbpcli.gbp import GBP
from gbpcli.types import Console
from rich import box
from rich.table import Table

HELP = "Search for files in packages"


def handler(args: argparse.Namespace, gbp: GBP, console: Console) -> int:
    """Search for files in packages"""
    machines: list[str] | None

    if args.machine:
        machines = [args.machine]
    elif args.mine:
        machines = utils.get_my_machines_from_args(args)
    else:
        machines = None

    data, _ = gbp.query.gbp_fl.searchv2(key=args.key, machines=machines)  # type: ignore

    if content_files := data["flSearchV2"]:
        table = create_table()
        row = table.add_row

        for item in content_files:
            if item["binpkg"]["build"]:
                row(*format_content_file(item, args))
        console.out.print(table)
    return 0


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Set subcommand arguments"""
    parser.add_argument(
        "--machine", "-m", default=None, help="Restrict search to the given machine"
    )
    parser.add_argument("--mine", action="store_true", default=False)
    parser.add_argument("key")


def create_table() -> Table:
    """Create table for displaying ContentFiles"""
    table = Table(box=box.ROUNDED, style="box")
    table.add_column("Size", justify="right", header_style="header")
    table.add_column("Timestamp", header_style="header")
    table.add_column("Package", header_style="header", overflow="fold")
    table.add_column("Path", header_style="header", overflow="fold")

    return table


def format_content_file(
    content_file: dict[str, Any], args: argparse.Namespace
) -> tuple[str, ...]:
    """Pretty-format the given content file giving args"""
    cf = SimpleNamespace(**content_file)
    binpkg = SimpleNamespace(**cf.binpkg)
    build = SimpleNamespace(**binpkg.build)
    machine = render.format_machine(build.machine, args)
    build_id = build.id.rsplit(".")[-1]
    timestamp = render.format_timestamp(
        dt.datetime.fromisoformat(cf.timestamp).astimezone(render.LOCAL_TIMEZONE)
    )
    return (
        f"[filesize]{cf.size}[/filesize]",
        f"[timestamp]{timestamp}[/timestamp]",
        (
            f"[machine]{machine}[/machine]"
            f"/[build_id]{build_id}[/build_id]"
            f"/[package]{binpkg.cpvb}"
        ),
        f"[tag]{cf.path}[/tag]",
    )
