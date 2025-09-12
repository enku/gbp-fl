"""gbp-fl

A pfl-inspired plugin for Gentoo Build Publisher.
"""

import importlib.metadata

__version__ = importlib.metadata.version("gbp-fl")

# Plugin definition
plugin = {
    "name": "gbp-fl",
    "app": "gbp_fl.django.gbp_fl.apps.GBPFLConfig",
    "description": "List and search build's package files",
    "version": __version__,
    "graphql": "gbp_fl.graphql",
    "priority": -10,
}
