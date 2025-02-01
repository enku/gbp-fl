"""Django Models for gbp-fl"""

import os.path
from typing import Any

from django.db import models


class ContentFile(models.Model):
    """DB backend for gbp-fl ContentFiles"""

    machine = models.CharField(max_length=255)
    build_id = models.CharField(max_length=255)
    path = models.CharField(max_length=1023)
    basename = models.CharField(max_length=255, db_index=True)
    cpvb = models.CharField(max_length=255)
    repo = models.CharField(max_length=127)
    size = models.IntegerField()
    timestamp = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "machine", "build_id", "cpvb", "path", name="unique_path"
            )
        ]
        indexes = [
            models.Index("machine", "build_id", name="idx_build"),
            models.Index("machine", "build_id", "cpvb", name="idx_build_cpvb"),
        ]
        get_latest_by = ["timestamp"]
        ordering = ["machine", "timestamp"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.basename = os.path.basename(self.path)

        super().save(*args, **kwargs)
