"""Async tasks for gbp-fl"""

# pylint: disable=import-outside-toplevel


def index_packages(machine: str, build_id: str) -> None:
    """Index packages for the given build"""
    import logging

    from gbp_fl import package_utils
    from gbp_fl.gateway import GBPGateway
    from gbp_fl.types import Build

    logger = logging.getLogger(__package__)
    build = Build(machine=machine, build_id=build_id)
    gbp = GBPGateway()

    logger.info("Saving packages for %s.%s", machine, build_id)
    gbp.set_process(build, "index")
    package_utils.index_packages(build)
    gbp.set_process(build, "clean")


def delete_from_build(machine: str, build_id: str) -> None:
    """Delete all the files from the given build"""
    from gbp_fl.gateway import GBPGateway
    from gbp_fl.records import Repo
    from gbp_fl.settings import Settings
    from gbp_fl.types import Build

    repo = Repo.from_settings(Settings.from_environ())
    files = repo.files
    build = Build(machine=machine, build_id=build_id)
    gbp = GBPGateway()

    gbp.set_process(build, "deindex")
    files.delete_from_build(machine, build_id)
    gbp.set_process(build, "clean")
