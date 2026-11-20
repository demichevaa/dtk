from typing import Optional

from databricks.sdk.runtime import dbutils

from dtk import SecretStore, make_secret


class DatabricksSecretStore:
    """dbutils.secrets.get(scope, key), cached per (scope, key)."""
    backend = "databricks"

    def __init__(self):
        self._cache: dict[tuple[str, str], str] = {}

    def get(self, scope: str, key: str) -> Optional[str]:
        if (scope, key) not in self._cache:
            try:
                value = dbutils.secrets.get(scope, key)
            except Exception:
                return None
            self._cache[(scope, key)] = value
        return self._cache[(scope, key)]


def make_secret_databricks(**overrides: str) -> SecretStore:
    return make_secret(DatabricksSecretStore(), **overrides)
