"""Extend the GBP Package type"""

from ariadne import ObjectType
from gentoo_build_publisher.types import Build, Package
from graphql import GraphQLResolveInfo

from gbp_fl.records import Repo
from gbp_fl.settings import Settings
from gbp_fl.types import ContentFile

type Info = GraphQLResolveInfo
PackageType = ObjectType("Package")


@PackageType.field("files")
def _(package: Package, _info: Info) -> list[ContentFile]:
    repo: Repo = Repo.from_settings(Settings.from_environ())
    build: Build = package.build

    return list(repo.files.for_package(build.machine, build.build_id, package.cpvb()))
