"""Template tags for gbp-fl"""

from typing import Any, cast

from django import template
from django.core.cache import cache

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import STATS_CACHE_KEY, FileStats, MachineStats

register = template.Library()


@register.simple_tag
def file_count() -> int:
    """Return the total number of files in the repo"""
    return get_stats().total


@register.simple_tag
def machine_file_count(machine: str) -> MachineStats:
    """Return the total and average file counts for the given machine"""
    by_machine = get_stats().by_machine

    return by_machine.get(machine, MachineStats())


@register.simple_tag
def gbp_fl_dashboard() -> dict[str, Any]:
    """Return the gbp-fl context for the dashboard view"""
    by_machine = get_stats().by_machine

    return {
        "files_by_machine": {
            machine: value.total for machine, value in by_machine.items()
        }
    }


def get_stats() -> FileStats:
    """Return the current FileStats

    If it's in the cache return the cached value.
    Otherwise calculate the value and cache it.
    """
    if stats := cache.get(STATS_CACHE_KEY):
        return cast(FileStats, stats)

    repo = Repo.from_settings(Settings.from_environ())
    stats = gateway.get_file_stats(repo)

    cache.set(STATS_CACHE_KEY, stats, timeout=None)

    return stats
