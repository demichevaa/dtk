import hashlib
import json
import uuid
from datetime import datetime
from pathlib import PurePosixPath
from types import ModuleType
from typing import NamedTuple

from .log import FATAL, LOG
from .runtime import RUNTIME
from .utc import utc_date, utc_iso, utc_now, utc_time

FORMAT_VERSION = 1


class ObjectStorage(NamedTuple):
    """backend: name for meta/logs. root: backend-specific root. io: module with uri/write_bytes/read_bytes/exists/list_keys(root, ...)."""
    backend: str
    root: str
    io: ModuleType


def check_key(key: str) -> str:
    if not key or key.startswith("/") or ".." in PurePosixPath(key).parts:
        FATAL("StorageKey(%s) invalid: must be relative, without '..'", key)
    return key


def uri(storage: ObjectStorage, key: str) -> str:
    return storage.io.uri(storage.root, key)


def write_bytes(storage: ObjectStorage, key: str, data: bytes) -> None:
    storage.io.write_bytes(storage.root, key, data)


def read_bytes(storage: ObjectStorage, key: str) -> bytes:
    return storage.io.read_bytes(storage.root, key)


def exists(storage: ObjectStorage, key: str) -> bool:
    return storage.io.exists(storage.root, key)


def list_keys(storage: ObjectStorage, prefix: str = "") -> list:
    return storage.io.list_keys(storage.root, prefix)


def OBJECT_NAME(prefix: str, at_utc: datetime, suffix: str = "") -> str:
    """prefix/YYYY-MM-DD/HHMMSS.ffffffZ[.suffix], UTC. No extension: the format adds it."""
    name = f"{prefix.strip('/')}/{utc_date(at_utc)}/{utc_time(at_utc)}"
    return check_key(f"{name}.{suffix}" if suffix else name)


def _meta_key(name: str) -> str:
    return f"{name}.meta.json"


def _json_default(o):
    return utc_iso(o) if isinstance(o, datetime) else str(o)


def write_with_meta(storage: ObjectStorage, name: str, data: bytes, meta: dict, fmt: str = "json") -> dict:
    """Writes <name>.<fmt>, then <name>.meta.json {storage, runtime, meta} as the commit marker."""
    data_key = f"{name}.{fmt}"
    system = {
        "format_version": FORMAT_VERSION,
        "id": str(uuid.uuid4()),
        "backend": storage.backend,
        "name": name,
        "format": fmt,
        "uri": uri(storage, data_key),
        "meta_uri": uri(storage, _meta_key(name)),
        "written_at_utc": utc_now(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    write_bytes(storage, data_key, data)
    write_bytes(
        storage,
        _meta_key(name),
        json.dumps({"storage": system, "runtime": RUNTIME(), "meta": meta}, default=_json_default, indent=2).encode("utf-8"),
    )
    LOG("Object(%s) written to Storage(%s): %s bytes", data_key, storage.backend, system["bytes"])
    return system


def read_meta(storage: ObjectStorage, name: str) -> dict:
    return json.loads(read_bytes(storage, _meta_key(name)))
