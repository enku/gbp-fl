"""Extend the GBP Package type"""

from ariadne import ObjectType
from gentoo_build_publisher.types import Package
from graphql import GraphQLResolveInfo

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import BinPkg, ContentFile

type Info = GraphQLResolveInfo
PACKAGE = ObjectType("Package")


@PACKAGE.field("files")
def files(package: BinPkg | Package, _info: Info) -> list[ContentFile]:
    """Return all ContentFiles for the given package"""
    repo: Repo = Repo.from_settings(Settings.from_environ())
    build = package.build

    return list(repo.files.for_package(build.machine, build.build_id, package.cpvb()))


@PACKAGE.field("cpvb")
def cpvb(package: BinPkg | Package, _info: Info) -> str:
    """return cpvb for the given package"""
    return package.cpvb()
