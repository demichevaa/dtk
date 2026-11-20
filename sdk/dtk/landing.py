import hashlib
import json
import uuid
from datetime import datetime

from .log import LOG
from .runtime import RUNTIME
from .storage import ObjectStorage, check_key
from .utc import utc_date, utc_iso, utc_now, utc_time

FORMAT_VERSION = 1


def landing_key_by_ts(prefix: str, at_utc: datetime, suffix: str = "") -> str:
    """prefix/YYYY-MM-DD/HHMMSS.ffffffZ[.suffix]"""
    name = f"{prefix.strip('/')}/{utc_date(at_utc)}/{utc_time(at_utc)}"
    return check_key(f"{name}.{suffix}" if suffix else name)


def _meta_key(name: str) -> str:
    return f"{name}.meta.json"


def _json_default(o):
    return utc_iso(o) if isinstance(o, datetime) else str(o)


def land(storage: ObjectStorage, name: str, data: bytes, meta: dict, fmt: str = "json") -> dict:
    """Writes <name>.<fmt>, then <name>.meta.json {storage, runtime, meta} as the commit marker."""
    data_key = f"{name}.{fmt}"
    system = {
        "format_version": FORMAT_VERSION,
        "id": str(uuid.uuid4()),
        "backend": storage.backend,
        "name": name,
        "format": fmt,
        "uri": storage.uri(data_key),
        "meta_uri": storage.uri(_meta_key(name)),
        "written_at_utc": utc_now(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    storage.write_bytes(data_key, data)
    storage.write_bytes(
        _meta_key(name),
        json.dumps({"storage": system, "runtime": RUNTIME(), "meta": meta}, default=_json_default, indent=2).encode("utf-8"),
    )
    LOG("Object(%s) written to Storage(%s): %s bytes", data_key, storage.backend, system["bytes"])
    return system


def read_landed_meta(storage: ObjectStorage, name: str) -> dict:
    return json.loads(storage.read_bytes(_meta_key(name)))
