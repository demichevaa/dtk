import os
from typing import Optional

from .log import FATAL


def _read_env(scope: str, key: str) -> Optional[str]:
    return os.environ.get(f"{scope}_{key}".upper().replace("-", "_"))


def _read_databricks(scope: str, key: str) -> Optional[str]:
    from databricks.sdk.runtime import dbutils
    try:
        return dbutils.secrets.get(scope, key)
    except Exception:
        return None


_BACKENDS = {"env": _read_env, "databricks": _read_databricks}


def _default_backend() -> str:
    if os.environ.get("SDK_SECRET_BACKEND"):
        return os.environ["SDK_SECRET_BACKEND"]
    return "databricks" if "DATABRICKS_RUNTIME_VERSION" in os.environ else "env"


class SecretScope:
    def __init__(self, store: "SecretStore", name: str):
        self._store, self._name = store, name

    def __getitem__(self, key: str) -> Optional[str]:
        """None if missing: SECRET[scope][key] or default / or FATAL(...)."""
        return self._store.find(self._name, key)


class SecretStore:
    def __init__(self, backend: str):
        if backend not in _BACKENDS:
            FATAL("Secret(%s) unknown backend: expected one of %s", backend, list(_BACKENDS))
        self.backend = backend
        self._read = _BACKENDS[backend]
        self._cache: dict[tuple[str, str], str] = {}

    def __getitem__(self, scope: str) -> SecretScope:
        return SecretScope(self, scope)

    def find(self, scope: str, key: str) -> Optional[str]:
        if (scope, key) not in self._cache:
            value = self._read(scope, key)
            if value is None:
                return None
            self._cache[(scope, key)] = value
        return self._cache[(scope, key)]


def new_secret_store(backend: Optional[str] = None) -> SecretStore:
    return SecretStore(backend or _default_backend())


_global: Optional[SecretStore] = None


def SECRET_INIT(backend: str) -> SecretStore:
    global _global
    if _global is not None and _global.backend != backend:
        FATAL("Secret(%s) already in use, can't switch to %s", _global.backend, backend)
    _global = _global or new_secret_store(backend)
    return _global


class _GlobalSecret:
    def __getitem__(self, scope: str) -> SecretScope:
        global _global
        if _global is None:
            _global = new_secret_store()
        return _global[scope]


SECRET = _GlobalSecret()
