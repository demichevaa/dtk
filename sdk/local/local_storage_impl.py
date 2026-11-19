import os
import sys
from pathlib import Path, PurePosixPath

from ..storage import ObjectStorage, check_key


def make_local_storage(root: str) -> ObjectStorage:
    return ObjectStorage("local", str(Path(root).resolve()), sys.modules[__name__])


def _path(root: str, key: str) -> Path:
    return Path(root).joinpath(*PurePosixPath(check_key(key)).parts)


def uri(root: str, key: str) -> str:
    return str(_path(root, key))


def write_bytes(root: str, key: str, data: bytes) -> None:
    target = _path(root, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, target)


def read_bytes(root: str, key: str) -> bytes:
    return _path(root, key).read_bytes()


def exists(root: str, key: str) -> bool:
    return _path(root, key).exists()


def list_keys(root: str, prefix: str = "") -> list:
    base = Path(root)
    start = _path(root, prefix) if prefix else base
    if not start.exists():
        return []
    return sorted(p.relative_to(base).as_posix() for p in start.rglob("*") if p.is_file() and not p.name.startswith("."))
