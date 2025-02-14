"""GraphQL interface for gbp-fl"""

from importlib import resources

from ariadne import gql

from .binpkg import BinPkgType
from .content_file import ContentFileType
from .mutations import Mutation
from .queries import Query

type_defs = gql(resources.read_text("gbp_fl.graphql", "schema.graphql"))
resolvers = [BinPkgType, ContentFileType, Query, Mutation]
