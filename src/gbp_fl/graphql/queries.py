"""The Query GraphQL type for gbp-fl"""

from typing import Any, TypeAlias

from ariadne import ObjectType, convert_kwargs_to_snake_case
from graphql import GraphQLResolveInfo

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import ContentFile

Info: TypeAlias = GraphQLResolveInfo
Query = ObjectType("Query")

# pylint: disable=missing-docstring


@Query.field("flSearch")
def _(
    _obj: Any, _info: Info, *, key: str, machine: str | None = None
) -> list[ContentFile]:
    files = get_repo().files

    return list(files.search(key, machine))


@Query.field("flCount")
@convert_kwargs_to_snake_case
def _(
    _obj: Any, _info: Info, *, machine: str | None = None, build_id: str | None = None
) -> int:
    files = get_repo().files

    return files.count(machine, build_id, None)


@Query.field("flList")
@convert_kwargs_to_snake_case
def _(
    _obj: Any, _info: Info, *, machine: str, build_id: str, cpvb: str
) -> list[ContentFile]:
    files = get_repo().files

    return list(files.for_package(machine, build_id, cpvb))


def get_repo() -> Repo:
    return Repo.from_settings(Settings.from_environ())
