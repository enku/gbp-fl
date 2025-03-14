"""GraphQL interface for gbp-fl"""

from importlib import resources

from ariadne import gql

from .binpkg import flBinPkg
from .content_file import flContentFile
from .mutations import Mutation
from .queries import Query

type_defs = gql(resources.read_text("gbp_fl.graphql", "schema.graphql"))
resolvers = [flBinPkg, flContentFile, Query, Mutation]
