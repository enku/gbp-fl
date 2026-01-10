"""The Query GraphQL type for gbp-fl"""

import datetime as dt
from functools import partial
from typing import Any, TypeAlias, TypedDict

from ariadne import ObjectType, convert_kwargs_to_snake_case
from graphql import GraphQLResolveInfo

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, ContentFile

Info: TypeAlias = GraphQLResolveInfo
QUERY = ObjectType("Query")

# pylint: disable=missing-docstring


class GQLMachineStats(TypedDict):
    machine: str
    total: int
    build_count: int
    per_build: int


class GQLFileStats(TypedDict):
    total: int
    by_machine: list[GQLMachineStats]


@QUERY.field("flSearch")
def fl_search(
    _obj: Any, _info: Info, *, key: str, machine: str | None = None
) -> list[ContentFile]:
    repo = Repo.from_settings(Settings.from_environ())

    return list(repo.files.search(key, [machine] if machine else None))


@QUERY.field("flSearchV2")
def fl_search_v2(
    _obj: Any, _info: Info, *, key: str, machines: list[str] | None = None
) -> list[ContentFile]:
    repo = Repo.from_settings(Settings.from_environ())

    return list(repo.files.search(key, machines))


@QUERY.field("flCount")
@convert_kwargs_to_snake_case
def fl_count(
    _obj: Any, _info: Info, *, machine: str | None = None, build_id: str | None = None
) -> int:
    repo = Repo.from_settings(Settings.from_environ())

    return repo.files.count(machine, build_id, None)


@QUERY.field("flList")
@convert_kwargs_to_snake_case
def fl_list(
    _obj: Any, _info: Info, *, machine: str, build_id: str, cpvb: str
) -> list[ContentFile]:
    repo = Repo.from_settings(Settings.from_environ())

    return list(repo.files.for_package(machine, build_id, cpvb))


@QUERY.field("flListPackages")
@convert_kwargs_to_snake_case
def fl_list_packages(
    _obj: Any, _info: Info, *, machine: str, build_id: str
) -> list[BinPkg]:
    build = Build(machine=machine, build_id=build_id)
    time = partial(dt.datetime.fromtimestamp, tz=dt.UTC)

    return [
        BinPkg(
            build=build,
            cpv=p.cpv,
            build_id=p.build_id,
            repo=p.repo,
            build_time=time(p.build_time),
        )
        for p in gateway.get_packages(build)
    ]


@QUERY.field("flStats")
def fl_stats(_obj: Any, _info: Info) -> GQLFileStats:
    stats = gateway.get_cached_stats()
    assert stats

    return {
        "total": stats.total,
        "by_machine": [
            {
                "machine": machine,
                "total": ms.total,
                "per_build": ms.per_build,
                "build_count": ms.build_count,
            }
            for machine, ms in stats.by_machine.items()
        ],
    }
