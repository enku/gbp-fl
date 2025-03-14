"""The GraphQL BinPkg type for gbp-fl"""

import re
from typing import TypeAlias

from ariadne import ObjectType
from django.http import HttpRequest
from graphql import GraphQLResolveInfo

from gbp_fl.gateway import GBPGateway
from gbp_fl.types import BinPkg, Build, BuildLike

flBinPkg = ObjectType("flBinPkg")
Info: TypeAlias = GraphQLResolveInfo


# Version regex for cpv's
V_RE = re.compile("-[0-9]")

# pylint: disable=missing-docstring


@flBinPkg.field("build")
def _(pkg: BinPkg, _info: Info) -> BuildLike:
    build = pkg.build
    gbp = GBPGateway()

    return gbp.get_build_record(Build(machine=build.machine, build_id=build.build_id))


@flBinPkg.field("url")
def _(pkg: BinPkg, info: Info) -> str:
    cpv = pkg.cpv
    c, pv = cpv.split("/", 1)

    v_match = V_RE.search(pv)
    assert v_match is not None
    p = pv[: v_match.start()]
    request: HttpRequest = info.context["request"]
    build = pkg.build

    return request.build_absolute_uri(
        f"/machines/{build.machine}/builds/{build.build_id}/packages/{c}/{p}"
        f"/{pv}-{pkg.build_id}"
    )
