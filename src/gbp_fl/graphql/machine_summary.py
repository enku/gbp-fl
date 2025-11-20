"""Extended GBP MachineSummary"""

from ariadne import ObjectType
from gentoo_build_publisher.machines import MachineInfo
from graphql import GraphQLResolveInfo

from gbp_fl.gateway import gateway
from gbp_fl.types import MachineStats

type Info = GraphQLResolveInfo
MachineSummary = ObjectType("MachineSummary")


@MachineSummary.field("fileStats")
def _(machine_info: MachineInfo, _info: Info) -> MachineStats:
    machine = machine_info.machine
    stats = gateway.get_cached_stats()
    assert stats

    return stats.by_machine[machine]
