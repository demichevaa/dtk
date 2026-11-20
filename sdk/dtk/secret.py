import os
from typing import Optional, Protocol

from .log import FATAL


class SecretStore(Protocol):
    """None if the secret is missing."""
    backend: str

    def get(self, scope: str, key: str) -> Optional[str]: ...


class EnvarSecretStore:
    """Env var <SCOPE>_<KEY>, uppercase, '-' -> '_'."""
    backend = "envar"

    def get(self, scope: str, key: str) -> Optional[str]:
        return os.environ.get(f"{scope}_{key}".upper().replace("-", "_"))


_store: Optional[SecretStore] = None
_overrides: dict[str, str] = {}


def make_secret(store: SecretStore, **overrides: str) -> SecretStore:
    """Installs the SECRET store, once per process. overrides: scope_key=value (lowercase, '-' -> '_'), checked before the store."""
    global _store, _overrides
    if _store is not None:
        FATAL("Secret(%s) already initialized, can't install Secret(%s)", _store.backend, store.backend)
    _store, _overrides = store, {k.lower(): v for k, v in overrides.items()}
    return store


def make_secret_envar(**overrides: str) -> SecretStore:
    return make_secret(EnvarSecretStore(), **overrides)


class SecretScope:
    def __init__(self, store: SecretStore, name: str):
        self._store, self._name = store, name

    def __getitem__(self, key: str) -> Optional[str]:
        """None if missing: SECRET[scope][key] or default / or FATAL(...)."""
        name = f"{self._name}_{key}".lower().replace("-", "_")
        if name in _overrides:
            return _overrides[name]
        return self._store.get(self._name, key)


class _GlobalSecret:
    def __getitem__(self, scope: str) -> SecretScope:
        if _store is None:
            FATAL("Secret(%s) not initialized: call make_secret_envar(), make_secret_databricks() or make_secret() first", scope)
        return SecretScope(_store, scope)


SECRET = _GlobalSecret()
