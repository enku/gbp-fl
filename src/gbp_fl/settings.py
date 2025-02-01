"""Settings for gbp-fl"""

from dataclasses import dataclass

from gbpcli.settings import BaseSettings


@dataclass(frozen=True)
class Settings(BaseSettings):
    """gbp-fl Settings"""

    env_prefix = "GBP_FL_"

    # pylint: disable=invalid-name
    RECORDS_BACKEND: str = "memory"
    RECORDS_BACKEND_DJANGO_BULK_BATCH_SIZE: int = 300
