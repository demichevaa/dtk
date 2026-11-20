"""
LOG / FATAL, printf-style. FATAL logs and raises FatalError; SDK_FATAL_EXIT=1 exits instead.
SDK_LOG_FORMAT: str.format template with {ts} (UTC datetime), {ts_local} (local datetime), {msg}.
"""

import os
import sys
from typing import NoReturn

from .exceptions import FatalError
from .utc import utc_now

DEFAULT_FORMAT = "{ts:%Y-%m-%dT%H:%M:%S.%fZ} {msg}"


def _emit(msg: str) -> None:
    now = utc_now()
    line = (os.environ.get("SDK_LOG_FORMAT") or DEFAULT_FORMAT).format(ts=now, ts_local=now.astimezone(), msg=msg)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def LOG(fmt: str, *args) -> None:
    _emit(fmt % args if args else fmt)


def FATAL(fmt: str, *args) -> NoReturn:
    msg = fmt % args if args else fmt
    _emit(msg)
    if os.environ.get("SDK_FATAL_EXIT") == "1":
        sys.exit(1)
    raise FatalError(msg)
