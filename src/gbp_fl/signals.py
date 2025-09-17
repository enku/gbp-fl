"""gbp-fl signal handlers"""

from typing import Any, Callable, TypeAlias

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BuildLike
from gbp_fl.worker import tasks

Receiver: TypeAlias = Callable[..., Any]


def gbp_build_pulled(*, build: BuildLike, **kwargs: Any) -> None:
    """Save the pulled build's package files to the database"""
    gateway.run_task(tasks.index_build, build.machine, build.build_id)


def gbp_build_deleted(*, build: BuildLike) -> None:
    """Signal handler for the deleting of builds

    Delete all the ContentFiles associated with the given build.
    """
    gateway.run_task(tasks.deindex_build, build.machine, build.build_id)


def cache_stats(**_kwargs: Any) -> None:
    """Signal handler for the the the postindex/postdeindex events

    Updates the stats cache.
    """
    repo = Repo.from_settings(Settings.from_environ())

    gateway.cache_file_stats(gateway.get_file_stats(repo))


def init() -> None:
    """Initialize"""
    gateway.register_signal("gbp_fl_preindex")
    gateway.register_signal("gbp_fl_postindex")
    gateway.register_signal("gbp_fl_predeindex")
    gateway.register_signal("gbp_fl_postdeindex")

    gateway.receive_signal(gbp_build_pulled, "postpull")
    gateway.receive_signal(gbp_build_deleted, "postdelete")
    gateway.receive_signal(cache_stats, "gbp_fl_postindex")
    gateway.receive_signal(cache_stats, "gbp_fl_postdeindex")
