"""GraphQL interface for gbp-fl"""

# pylint: disable=missing-docstring

import re
from importlib import resources
from typing import Any

from ariadne import ObjectType, convert_kwargs_to_snake_case, gql
from django.http import HttpRequest
from graphql import GraphQLResolveInfo

from gbp_fl.gateway import GBPGateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, BuildLike, ContentFile

# Version regex for cpv's
V_RE = re.compile("-[0-9]")

type_defs = gql(resources.read_text("gbp_fl", "schema.graphql"))
resolvers = [
    binpkg := ObjectType("flBinPkg"),
    content_file := ObjectType("flContentFile"),
    query := ObjectType("Query"),
    mutation := ObjectType("Mutation"),
]


@query.field("flSearch")
def resolve_file_list_search(
    _obj: Any, _info: GraphQLResolveInfo, *, key: str, machine: str | None = None
) -> list[ContentFile]:
    files = get_repo().files

    return list(files.search(key, machine))


@query.field("flCount")
@convert_kwargs_to_snake_case
def resolve_file_list_count(
    _obj: Any,
    _info: GraphQLResolveInfo,
    *,
    machine: str | None = None,
    build_id: str | None = None,
) -> int:
    files = get_repo().files

    return files.count(machine, build_id, None)


@binpkg.field("build")
def resolve_binpkg_build(pkg: BinPkg, _info: GraphQLResolveInfo) -> BuildLike:
    build = pkg.build
    gbp = GBPGateway()

    return gbp.get_build_record(Build(machine=build.machine, build_id=build.build_id))


@binpkg.field("url")
def resolve_binpkg_url(pkg: BinPkg, info: GraphQLResolveInfo) -> str:
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


def get_repo() -> Repo:
    return Repo.from_settings(Settings.from_environ())
