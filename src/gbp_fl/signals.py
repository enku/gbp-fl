"""gbp-fl signal handlers"""

from typing import Any, Callable, TypeAlias

from gbp_fl.gateway import GBPGateway
from gbp_fl.types import BuildLike
from gbp_fl.worker import tasks

Receiver: TypeAlias = Callable[..., Any]


def gbp_build_pulled(*, build: BuildLike, **kwargs: Any) -> None:
    """Save the pulled build's package files to the database"""
    gbp = GBPGateway()

    gbp.run_task(tasks.index_packages, build.machine, build.build_id)


def gbp_build_deleted(*, build: BuildLike) -> None:
    """Signal handler for the deleting of builds

    Delete all the ContentFiles associated with the given build.
    """
    gbp = GBPGateway()

    gbp.run_task(tasks.delete_from_build, build.machine, build.build_id)


def init() -> None:
    """Initialize"""
    gbp = GBPGateway()
    gbp.receive_signal(gbp_build_pulled, "postpull")
    gbp.receive_signal(gbp_build_deleted, "postdelete")
