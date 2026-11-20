import os
from pathlib import Path, PurePosixPath
from typing import Protocol

from .log import FATAL


class ObjectStorage(Protocol):
    """Keys are relative POSIX paths (check_key). write_bytes is all-or-nothing per object."""
    backend: str

    def uri(self, key: str) -> str: ...
    def write_bytes(self, key: str, data: bytes) -> None: ...
    def read_bytes(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def list_keys(self, prefix: str = "") -> list[str]: ...


def check_key(key: str) -> str:
    if not key or key.startswith("/") or ".." in PurePosixPath(key).parts:
        FATAL("StorageKey(%s) invalid: must be relative, without '..'", key)
    return key


class LocalStorage:
    backend = "local"

    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        return self.root.joinpath(*PurePosixPath(check_key(key)).parts)

    def uri(self, key: str) -> str:
        return str(self._path(key))

    def write_bytes(self, key: str, data: bytes) -> None:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list_keys(self, prefix: str = "") -> list[str]:
        start = self._path(prefix) if prefix else self.root
        if not start.exists():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in start.rglob("*") if p.is_file() and not p.name.startswith("."))


def make_storage_local(root: str) -> ObjectStorage:
    return LocalStorage(root)
