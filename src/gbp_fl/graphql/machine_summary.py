"""Extended GBP MachineSummary"""

from typing import cast

from ariadne import ObjectType
from gentoo_build_publisher.cache import cache
from gentoo_build_publisher.machines import MachineInfo
from graphql import GraphQLResolveInfo

from gbp_fl.types import STATS_CACHE_KEY, FileStats, MachineStats

type Info = GraphQLResolveInfo
MachineSummary = ObjectType("MachineSummary")


@MachineSummary.field("fileStats")
def _(machine_info: MachineInfo, _info: Info) -> MachineStats:
    machine = machine_info.machine
    stats = cast(FileStats, cache.get(STATS_CACHE_KEY))

    return stats.by_machine[machine]
