"""Template tags for gbp-fl"""

import hashlib
from typing import Any, Iterable, cast

from django import template
from django.core.cache import cache

from gbp_fl.records import Repo
from gbp_fl.settings import Settings

register = template.Library()


@register.simple_tag
def file_count() -> int:
    """Return the total number of files in the repo"""
    if count := cache.get("file-count"):
        return cast(int, count)

    repo = Repo.from_settings(Settings.from_environ())
    count = repo.files.count(  # pylint: disable=assignment-from-no-return
        None, None, None
    )
    cache.set("file-count", count, timeout=1800)

    return count


@register.simple_tag
def machine_file_count(machine: str, build_count: int) -> dict[str, int]:
    """Return the total and average file counts for the given machine

    Returns a dict like:

        {
            "total": 50000,      # total count of files for the machine
            "per_build": 10000,  # average number of files per machine's builds
        }
    """
    repo = Repo.from_settings(Settings.from_environ())
    count = repo.files.count(  # pylint: disable=assignment-from-no-return
        machine, None, None
    )
    return {"total": count, "per_build": count // build_count}


@register.simple_tag
def gbp_fl_dashboard(machines: Iterable[str]) -> dict[str, Any]:
    """Return the gbp-fl context for the dashboard view"""
    machines = sorted(set(machines))
    joined = "".join(machines)
    my_hash = hashlib.sha256(joined.encode()).hexdigest()
    key = f"gbp-fl-dashboard.{my_hash}"

    if stats := cache.get(key):
        return cast(dict[str, Any], stats)

    repo = Repo.from_settings(Settings.from_environ())
    files_by_machine = {
        machine: repo.files.count(machine, None, None) for machine in machines
    }
    stats = {"files_by_machine": files_by_machine}
    cache.set(key, stats, timeout=1800)

    return stats
