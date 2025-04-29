"""The GraphQL BinPkg type for gbp-fl"""

import re
from typing import TypeAlias

from ariadne import ObjectType
from django.http import HttpRequest
from django.urls import reverse
from graphql import GraphQLResolveInfo

from gbp_fl.gateway import gateway
from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, Build, BuildLike, ContentFile

flBinPkg = ObjectType("flBinPkg")
Info: TypeAlias = GraphQLResolveInfo


# Version regex for cpv's
V_RE = re.compile("-[0-9]")

# pylint: disable=missing-docstring


@flBinPkg.field("build")
def _(pkg: BinPkg, _info: Info) -> BuildLike:
    build = pkg.build

    return gateway.get_build_record(
        Build(machine=build.machine, build_id=build.build_id)
    )


@flBinPkg.field("url")
def _(pkg: BinPkg, info: Info) -> str | None:
    request: HttpRequest = info.context["request"]
    c, pv = pkg.cpv.split("/", 1)

    v_match = V_RE.search(pv)
    assert v_match
    build = pkg.build
    view_args = {
        "machine": build.machine,
        "build_id": build.build_id,
        "c": c,
        "p": pv[: v_match.start()],
        "pv": pv,
        "b": pkg.build_id,
    }
    return request.build_absolute_uri(reverse("gbp-binpkg", kwargs=view_args))


@flBinPkg.field("files")
def _(pkg: BinPkg, _info: Info) -> list[ContentFile]:
    repo = Repo.from_settings(Settings.from_environ())
    return list(repo.files.for_package(pkg.build.machine, pkg.build.build_id, pkg.cpvb))
