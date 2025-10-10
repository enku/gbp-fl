"""GraphQL interface for gbp-fl"""

from importlib import resources

from ariadne import gql

from .binpkg import flBinPkg
from .content_file import flContentFile
from .machine_summary import MachineSummary
from .mutations import Mutation
from .packages import PackageType
from .queries import Query

type_defs = gql(resources.read_text("gbp_fl.graphql", "schema.graphql"))
resolvers = [MachineSummary, Mutation, PackageType, Query, flBinPkg, flContentFile]
