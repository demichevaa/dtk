"""Clocks and datetimes. Aware UTC only (naive raises), ISO 8601 with Z; durations on the monotonic clock."""

import time
from datetime import datetime, timezone


def _require_utc(dt: datetime) -> datetime:
    from .log import FATAL  # lazy: log imports utc
    if not isinstance(dt, datetime):
        FATAL("Datetime(%r) invalid: expected datetime, got %s", dt, type(dt).__name__)
    if dt.tzinfo is None or dt.utcoffset() is None:
        FATAL("Datetime(%r) is naive: zone unknown, use dtk.utc_now() or dtk.utc_from_epoch_s()", dt)
    return dt.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def mono_now_s() -> float:
    """Monotonic seconds, for durations only."""
    return time.monotonic()


def mono_elapsed_ms(since_s: float) -> int:
    """Milliseconds since a mono_now_s() reading."""
    return round((time.monotonic() - since_s) * 1000)


def utc_from_epoch_s(epoch_s: float) -> datetime:
    return datetime.fromtimestamp(epoch_s, timezone.utc)


def utc_to_epoch_s(dt: datetime) -> int:
    return int(_require_utc(dt).timestamp())


def utc_iso(dt: datetime) -> str:
    """2026-11-19T08:11:47.853369Z"""
    return _require_utc(dt).isoformat().replace("+00:00", "Z")


def utc_parse(text: str) -> datetime:
    """ISO 8601 with Z or an explicit offset -> aware UTC datetime. No offset -> ValueError."""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return _require_utc(datetime.fromisoformat(text))


def utc_date(dt: datetime) -> str:
    """2026-11-19"""
    return _require_utc(dt).strftime("%Y-%m-%d")


def utc_time(dt: datetime) -> str:
    """080806.260087Z"""
    return _require_utc(dt).strftime("%H%M%S.%fZ")
