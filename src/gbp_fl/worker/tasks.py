"""Async tasks for gbp-fl"""

# pylint: disable=import-outside-toplevel


def index_packages(machine: str, build_id: str) -> None:
    """Index packages for the given build"""
    import logging

    from gbp_fl import package_utils
    from gbp_fl.types import Build

    logger = logging.getLogger(__package__)
    build = Build(machine=machine, build_id=build_id)

    logger.info("Saving packages for %s.%s", machine, build_id)
    package_utils.index_packages(build)


def delete_from_build(machine: str, build_id: str) -> None:
    """Delete all the files from the given build"""
    from gbp_fl.records import Repo
    from gbp_fl.settings import Settings

    repo = Repo.from_settings(Settings.from_environ())
    files = repo.files

    files.delete_from_build(machine, build_id)
