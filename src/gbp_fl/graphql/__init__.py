"""GraphQL interface for gbp-fl"""

from importlib import resources

from ariadne import gql

from .content_file import FL_CONTENT_FILE
from .machine_summary import MACHINE_SUMMARY
from .mutations import MUTATION
from .packages import PACKAGE
from .queries import QUERY

type_defs = gql(resources.read_text("gbp_fl.graphql", "schema.graphql"))
resolvers = [MACHINE_SUMMARY, MUTATION, PACKAGE, QUERY, FL_CONTENT_FILE]
