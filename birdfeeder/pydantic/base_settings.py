import os
from typing import TypeVar

from pydantic import BaseSettings

BaseSettingsWithConfig_T = TypeVar("BaseSettingsWithConfig_T", bound="BaseSettingsWithConfig")


class BaseSettingsWithConfig(BaseSettings):
    class Config:
        secrets_dir = os.path.join(os.path.dirname(__file__), "secrets")
        env_file = ".env"

    @classmethod
    def for_env(cls, env: str) -> BaseSettingsWithConfig_T:
        """
        Loads local overrides from an environment-specific file.

        Examples:
        - .env.development
        - .env.staging
        - .env.production
        - .env.local
        """
        return cls(_env_file=f".env.{env.lower()}")
