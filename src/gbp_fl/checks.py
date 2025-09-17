"""gbp-fl checks for Gentoo Build Publisher"""

# Note that we do not exclusively use the gateway here because, in effect, this is a
# Gentoo Build Publisher utility, not a gbp-fl utility.


from gbpcli.types import Console
from gentoo_build_publisher import publisher
from gentoo_build_publisher.types import Build as GBPBuild

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings


def all_builds_have_indices(console: Console) -> tuple[int, int]:
    """Check that the indices are good"""
    warnings = 0
    repo = Repo.from_settings(Settings.from_environ())
    files = repo.files
    indexed_builds = set(files.get_builds())

    for machine in gateway.list_machine_names():
        for build in gateway.get_builds_for_machine(machine):
            if not build in indexed_builds:
                warnings += 1
                console.err.print(
                    f"Warning: build {build.machine}.{build.build_id} is not indexed."
                )

    return (0, warnings)


def all_indices_have_builds(console: Console) -> tuple[int, int]:
    """Check that all indices have a corresponding build"""
    warnings = 0
    repo = Repo.from_settings(Settings.from_environ())
    files = repo.files

    for build in files.get_builds():
        gbp_build = GBPBuild(machine=build.machine, build_id=build.build_id)
        if not publisher.pulled(gbp_build):
            console.err.print(
                f"Warning: an index exists for build {gbp_build} that does not exist."
            )
            warnings += 1

    return (0, warnings)
