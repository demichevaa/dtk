import os
from typing import Optional


def _read_env(scope: str, key: str) -> str:
    name = f"{scope}_{key}".upper().replace("-", "_")
    try:
        return os.environ[name]
    except KeyError:
        raise KeyError(f"secret {scope}/{key} not found: set env var {name}") from None


def _read_databricks(scope: str, key: str) -> str:
    from databricks.sdk.runtime import dbutils
    try:
        return dbutils.secrets.get(scope, key)
    except Exception as e:
        raise KeyError(f"secret {scope}/{key} not found in Databricks: {e}") from None


_BACKENDS = {"env": _read_env, "databricks": _read_databricks}


def _default_backend() -> str:
    if os.environ.get("SDK_SECRET_BACKEND"):
        return os.environ["SDK_SECRET_BACKEND"]
    return "databricks" if "DATABRICKS_RUNTIME_VERSION" in os.environ else "env"


class SecretScope:
    def __init__(self, store: "SecretStore", name: str):
        self._store, self._name = store, name

    def __getitem__(self, key: str) -> str:
        return self._store.read(self._name, key)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            return self[key]
        except KeyError:
            return default


class SecretStore:
    def __init__(self, backend: str):
        if backend not in _BACKENDS:
            raise ValueError(f"unknown secret backend {backend!r}, expected one of {list(_BACKENDS)}")
        self.backend = backend
        self._read = _BACKENDS[backend]
        self._cache: dict[tuple[str, str], str] = {}

    def __getitem__(self, scope: str) -> SecretScope:
        return SecretScope(self, scope)

    def read(self, scope: str, key: str) -> str:
        if (scope, key) not in self._cache:
            self._cache[(scope, key)] = self._read(scope, key)
        return self._cache[(scope, key)]


def new_secret_store(backend: Optional[str] = None) -> SecretStore:
    return SecretStore(backend or _default_backend())


_global: Optional[SecretStore] = None


def SECRET_INIT(backend: str) -> SecretStore:
    global _global
    if _global is not None and _global.backend != backend:
        raise RuntimeError(f"SECRET already in use with backend {_global.backend!r}")
    _global = _global or new_secret_store(backend)
    return _global


class _GlobalSecret:
    def __getitem__(self, scope: str) -> SecretScope:
        global _global
        if _global is None:
            _global = new_secret_store()
        return _global[scope]


SECRET = _GlobalSecret()
