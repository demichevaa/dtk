import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

import dtk


def get(url: str, *, params: Optional[dict] = None, headers: Optional[dict] = None,
        timeout: int = 60, ok: tuple = (200,)) -> tuple[bytes, dict]:
    """Returns (data, meta). Status not in ok, or network error -> dtk.FATAL."""
    full_url = f"{url}?{urllib.parse.urlencode(params)}" if params else url
    req = urllib.request.Request(full_url, headers=headers or {}, method="GET")

    fetched_at_utc = dtk.utc_now()
    started_s = dtk.mono_now_s()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, resp_headers, data = r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        status, resp_headers, data = e.code, e.headers, e.read()
    except (urllib.error.URLError, TimeoutError) as e:
        dtk.FATAL("HttpGet(%s) failed: %s after %s ms", url, getattr(e, "reason", e), dtk.mono_elapsed_ms(started_s))
    elapsed_ms = dtk.mono_elapsed_ms(started_s)

    if status not in ok:
        dtk.FATAL("HttpGet(%s) failed: %s in %s ms, body %s", url, status, elapsed_ms, data[:500])
    dtk.LOG("HttpGet(%s) %s in %s ms, %s bytes", url, status, elapsed_ms, len(data))
    return data, {
        "method": "GET",
        "url": url,
        "params": params or {},
        "fetched_at_utc": fetched_at_utc,
        "elapsed_ms": elapsed_ms,
        "status": status,
        "headers": {k.lower(): v for k, v in resp_headers.items()},
    }


def post(url: str, *, data: Optional[dict] = None, json_body: Any = None, headers: Optional[dict] = None,
         timeout: int = 60, ok: tuple = (200,)) -> tuple[bytes, dict]:
    """data -> form-encoded body, json_body -> JSON body. Returns (data, meta). Status not in ok, or network error -> dtk.FATAL."""
    req_headers = dict(headers or {})
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif json_body is not None:
        body = json.dumps(json_body).encode()
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")

    fetched_at_utc = dtk.utc_now()
    started_s = dtk.mono_now_s()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, resp_headers, content = r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        status, resp_headers, content = e.code, e.headers, e.read()
    except (urllib.error.URLError, TimeoutError) as e:
        dtk.FATAL("HttpPost(%s) failed: %s after %s ms", url, getattr(e, "reason", e), dtk.mono_elapsed_ms(started_s))
    elapsed_ms = dtk.mono_elapsed_ms(started_s)

    if status not in ok:
        dtk.FATAL("HttpPost(%s) failed: %s in %s ms, body %s", url, status, elapsed_ms, content[:500])
    dtk.LOG("HttpPost(%s) %s in %s ms, %s bytes", url, status, elapsed_ms, len(content))
    return content, {
        "method": "POST",
        "url": url,
        "fetched_at_utc": fetched_at_utc,
        "elapsed_ms": elapsed_ms,
        "status": status,
        "headers": {k.lower(): v for k, v in resp_headers.items()},
    }
