import hashlib
import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Optional

from .log import LOG
from .runtime import RUNTIME
from .utc import utc_date, utc_iso, utc_now, utc_time

FORMAT_VERSION = 1
DEFAULT_FORMAT = "json"


def _check_key(key: str) -> str:
    if not key or key.startswith("/") or ".." in PurePosixPath(key).parts:
        raise ValueError(f"invalid storage key {key!r}: must be relative, without '..'")
    return key


def OBJECT_NAME(prefix: str, at_utc: datetime, suffix: Optional[str] = None) -> str:
    """prefix/YYYY-MM-DD/HHMMSS.ffffffZ[.suffix], UTC. No extension: the storage format adds it."""
    name = f"{prefix.strip('/')}/{utc_date(at_utc)}/{utc_time(at_utc)}"
    return _check_key(f"{name}.{suffix}" if suffix else name)


def _meta_key(name: str) -> str:
    return f"{name}.meta.json"


def _json_default(o):
    return utc_iso(o) if isinstance(o, datetime) else str(o)


def _write_with_meta(storage, name: str, data: bytes, meta: dict, fmt: Optional[str] = None) -> dict:
    """Writes <name>.<format>, then <name>.meta.json {storage, runtime, meta} as the commit marker."""
    fmt = fmt or storage.format
    data_key = f"{name}.{fmt}"
    system = {
        "format_version": FORMAT_VERSION,
        "id": str(uuid.uuid4()),
        "backend": storage.backend,
        "name": name,
        "format": fmt,
        "path": storage.path(data_key),
        "meta_path": storage.path(_meta_key(name)),
        "written_at_utc": utc_now(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    storage.write_bytes(data_key, data)
    storage.write_text(
        _meta_key(name),
        json.dumps({"storage": system, "runtime": RUNTIME(), "meta": meta}, default=_json_default, indent=2),
    )
    LOG("Object(%s) written to Storage(%s): %s bytes", data_key, storage.backend, system["bytes"])
    return system


class LocalStorage:
    def __init__(self, root: str, backend: str = "local", fmt: str = DEFAULT_FORMAT):
        self.backend = backend
        self.format = fmt
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        return self.root.joinpath(*PurePosixPath(_check_key(key)).parts)

    def path(self, key: str) -> str:
        return str(self._path(key))

    def write_bytes(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        return str(path)

    def write_text(self, key: str, text: str) -> str:
        return self.write_bytes(key, text.encode("utf-8"))

    def write_with_meta(self, name: str, data: bytes, meta: dict, fmt: Optional[str] = None) -> dict:
        return _write_with_meta(self, name, data, meta, fmt)

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def read_meta(self, name: str) -> dict:
        return json.loads(self.read_bytes(_meta_key(name)))

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list(self, prefix: str = "") -> list[str]:
        base = self._path(prefix) if prefix else self.root
        if not base.exists():
            return []
        return sorted(
            p.relative_to(self.root).as_posix()
            for p in base.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        )


class DatabricksFilesStorage:
    def __init__(self, root: str, fmt: str = DEFAULT_FORMAT):
        from databricks.sdk import WorkspaceClient
        self.backend = "databricks_files"
        self.format = fmt
        self.root = root.rstrip("/")
        self._files = WorkspaceClient().files

    def _path(self, key: str) -> str:
        return f"{self.root}/{_check_key(key)}"

    def path(self, key: str) -> str:
        return self._path(key)

    def write_bytes(self, key: str, data: bytes) -> str:
        path = self._path(key)
        self._files.create_directory(path.rsplit("/", 1)[0])
        self._files.upload(path, io.BytesIO(data), overwrite=True)
        return path

    def write_text(self, key: str, text: str) -> str:
        return self.write_bytes(key, text.encode("utf-8"))

    def write_with_meta(self, name: str, data: bytes, meta: dict, fmt: Optional[str] = None) -> dict:
        return _write_with_meta(self, name, data, meta, fmt)

    def read_bytes(self, key: str) -> bytes:
        return self._files.download(self._path(key)).contents.read()

    def read_meta(self, name: str) -> dict:
        return json.loads(self.read_bytes(_meta_key(name)))

    def exists(self, key: str) -> bool:
        from databricks.sdk.errors import NotFound
        try:
            self._files.get_metadata(self._path(key))
            return True
        except NotFound:
            return False

    def list(self, prefix: str = "") -> list[str]:
        from databricks.sdk.errors import NotFound
        out, stack = [], [self._path(prefix) if prefix else self.root]
        while stack:
            folder = stack.pop()
            try:
                entries = list(self._files.list_directory_contents(folder))
            except NotFound:
                continue
            for e in entries:
                if e.is_directory:
                    stack.append(e.path.rstrip("/"))
                else:
                    out.append(e.path[len(self.root) + 1:])
        return sorted(out)


def _default_backend() -> str:
    if os.environ.get("SDK_OBJECT_STORAGE_BACKEND"):
        return os.environ["SDK_OBJECT_STORAGE_BACKEND"]
    return "databricks" if "DATABRICKS_RUNTIME_VERSION" in os.environ else "local"


def new_object_storage(backend: Optional[str] = None, root: Optional[str] = None, fmt: Optional[str] = None):
    backend = backend or _default_backend()
    root = root or os.environ.get("SDK_OBJECT_STORAGE_ROOT")
    fmt = fmt or os.environ.get("SDK_OBJECT_STORAGE_FORMAT") or DEFAULT_FORMAT

    if backend == "local":
        return LocalStorage(root or "./object_storage", fmt=fmt)

    if backend in ("databricks", "databricks_files"):
        if not root or not root.startswith("/Volumes/"):
            raise ValueError(f"{backend} storage needs root='/Volumes/<catalog>/<schema>/<volume>', got {root!r}")
        if backend == "databricks":
            return LocalStorage(root, backend="databricks", fmt=fmt)
        return DatabricksFilesStorage(root, fmt=fmt)

    raise ValueError(f"unknown storage backend {backend!r}, expected 'local', 'databricks' or 'databricks_files'")


_global = None


def OBJECT_STORAGE_INIT(backend: str, root: Optional[str] = None, fmt: Optional[str] = None):
    global _global
    if _global is not None and _global.backend != backend:
        raise RuntimeError(f"OBJECT_STORAGE already in use with backend {_global.backend!r}")
    if _global is None:
        _global = new_object_storage(backend, root, fmt)
    return _global


class _GlobalStorage:
    def __getattr__(self, name):
        global _global
        if _global is None:
            _global = new_object_storage()
        return getattr(_global, name)


OBJECT_STORAGE = _GlobalStorage()
