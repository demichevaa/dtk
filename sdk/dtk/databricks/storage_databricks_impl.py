import os
from pathlib import Path, PurePosixPath

from dtk import FATAL, ObjectStorage, check_key


class DatabricksVolumeStorage:
    """UC volume from Databricks compute: /Volumes/... is a plain filesystem there."""
    backend = "databricks_volume"

    def __init__(self, root: str):
        self.root = Path(root)

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


def make_storage_databricks(root: str) -> ObjectStorage:
    if not root.startswith("/Volumes/"):
        FATAL("Storage(databricks_volume, %s) invalid root: must be /Volumes/<catalog>/<schema>/<volume>[/...]", root)
    return DatabricksVolumeStorage(root)
