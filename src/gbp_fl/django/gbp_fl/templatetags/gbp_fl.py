"""Template tags for gbp-fl"""

from typing import cast

from django import template
from django.core.cache import cache

from gbp_fl.records import repo

register = template.Library()


@register.simple_tag
def file_count() -> int:
    """Return the total number of files in the repo"""
    if count := cache.get("file-count"):
        return cast(int, count)

    count = repo.files.count(None, None, None)
    cache.set("file-count", count, timeout=1800)

    return count
