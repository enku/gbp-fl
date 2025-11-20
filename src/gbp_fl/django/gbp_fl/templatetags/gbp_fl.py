"""Template tags for gbp-fl"""

from dataclasses import asdict
from typing import Any

from django import template

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import FileStats, MachineStats

register = template.Library()


@register.simple_tag
def machine_file_count(machine: str) -> MachineStats:
    """Return the total and average file counts for the given machine"""
    by_machine = get_stats().by_machine

    return by_machine.get(machine, MachineStats())


@register.simple_tag
def file_stats() -> dict[str, Any]:
    """Return the current FileStats"""
    return asdict(get_stats())


def get_stats() -> FileStats:
    """Return the current FileStats

    If it's in the cache return the cached value.
    Otherwise calculate the value and cache it.
    """
    if stats := gateway.get_cached_stats():
        return stats

    repo = Repo.from_settings(Settings.from_environ())
    gateway.set_cached_stats(stats := gateway.get_file_stats(repo))

    return stats
