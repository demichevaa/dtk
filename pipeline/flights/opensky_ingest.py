import sys
from datetime import datetime

from connector import http, opensky
from sdk import FATAL, OBJECT_NAME, SECRET, ObjectStorage, utc_parse, utc_to_epoch_s, write_with_meta
from sdk.local import make_local_storage


def states_all(storage: ObjectStorage) -> None:
    token = opensky.token(
        SECRET["opensky"]["client_id"] or FATAL("Secret(opensky/client_id) not set"),
        SECRET["opensky"]["client_secret"] or FATAL("Secret(opensky/client_secret) not set"),
    )
    data, meta = http.get(
        f"{opensky.API_URL}/states/all",
        params={"extended": 1},
        headers=opensky.headers(token),
        ok=(200,),
    )
    write_with_meta(storage, OBJECT_NAME("opensky/states_all", meta["fetched_at_utc"]), data, meta)


def flights_all(storage: ObjectStorage, begin_utc: datetime, end_utc: datetime) -> None:
    """Interval max 2h; previous day or older (OpenSky computes flights nightly)."""
    token = opensky.token(
        SECRET["opensky"]["client_id"] or FATAL("Secret(opensky/client_id) not set"),
        SECRET["opensky"]["client_secret"] or FATAL("Secret(opensky/client_secret) not set"),
    )
    data, meta = http.get(
        f"{opensky.API_URL}/flights/all",
        params={"begin": utc_to_epoch_s(begin_utc), "end": utc_to_epoch_s(end_utc)},
        headers=opensky.headers(token),
        ok=(200,),
    )
    write_with_meta(storage, OBJECT_NAME("opensky/flights_all", meta["fetched_at_utc"]), data, meta)


def flights_arrival(storage: ObjectStorage, airport_icao: str, begin_utc: datetime, end_utc: datetime) -> None:
    """Interval max 2 days; previous day or older (OpenSky computes flights nightly)."""
    token = opensky.token(
        SECRET["opensky"]["client_id"] or FATAL("Secret(opensky/client_id) not set"),
        SECRET["opensky"]["client_secret"] or FATAL("Secret(opensky/client_secret) not set"),
    )
    data, meta = http.get(
        f"{opensky.API_URL}/flights/arrival",
        params={"airport": airport_icao, "begin": utc_to_epoch_s(begin_utc), "end": utc_to_epoch_s(end_utc)},
        headers=opensky.headers(token),
        ok=(200,),
    )
    write_with_meta(storage, OBJECT_NAME(f"opensky/flights_arrival/{airport_icao}", meta["fetched_at_utc"]), data, meta)


if __name__ == "__main__":
    # opensky_ingest.py                                       -> states_all
    # opensky_ingest.py flights_all BEGIN END                 -> BEGIN/END ISO 8601 UTC, e.g. 2026-11-18T00:00:00Z
    # opensky_ingest.py flights_arrival AIRPORT BEGIN END     -> AIRPORT ICAO, e.g. EDDF
    storage = make_local_storage("./object_storage")

    states_all(storage)
