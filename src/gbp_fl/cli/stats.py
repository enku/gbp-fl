"""Display gbp-fl statistics"""

import argparse
import locale
from typing import Any

from gbpcli import render, utils
from gbpcli.gbp import GBP
from gbpcli.graphql import check
from gbpcli.types import Console
from rich import box
from rich.table import Table

HELP = "Display builds' file statistics"


def handler(args: argparse.Namespace, gbp: GBP, console: Console) -> int:
    """Display the builds' file statistics"""
    graphql = gbp.query
    query_result = graphql.gbp_fl.stats()  # type: ignore[attr-defined]
    stats = check(query_result)["flStats"]

    print_stats(stats, args, console)

    return 0


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Build command-line arguments"""
    parser.add_argument("--mine", action="store_true", default=False)


def print_stats(
    stats: dict[str, Any], args: argparse.Namespace, console: Console
) -> None:
    """Print the given file stats to the console's standard output"""
    if args.mine:
        # The server API does not accept a list of machines because there is no
        # performance difference between sending the entire stats or stats for an
        # individual machine.  Therefore we will to the filtering client-side.
        mine = utils.get_my_machines_from_args(args)
        machines = [ms for ms in stats["byMachine"] if ms["machine"] in mine]
        total = sum(ms["total"] for ms in machines if ms["machine"] in mine)
    else:
        machines = stats["byMachine"]
        total = stats["total"]

    locale.setlocale(locale.LC_NUMERIC, "")

    table = Table(
        box=box.ROUNDED, style="box", title=f"{total:n} Files", title_style="header"
    )
    table.add_column("Machine", header_style="header")
    table.add_column("Files", justify="right", header_style="header")
    table.add_column("Per Build", justify="right", header_style="header")

    for ms in machines:
        machine = render.format_machine(ms["machine"], args)
        table.add_row(machine, f"{ms['total']:n}", f"{ms['perBuild']:n}")

    console.out.print(table)
