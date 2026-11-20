import sys
from datetime import datetime

from dtk.connector import http, opensky
from dtk import FATAL, SECRET, ObjectStorage, land, landing_key_by_ts, utc_parse, utc_to_epoch_s


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
    land(storage, landing_key_by_ts("opensky/states_all", meta["fetched_at_utc"]), data, meta)


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
    land(storage, landing_key_by_ts("opensky/flights_all", meta["fetched_at_utc"]), data, meta)


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
    
    land(storage, landing_key_by_ts(f"opensky/flights_arrival/{airport_icao}", meta["fetched_at_utc"]), data, meta)


if __name__ == "__main__":
    # opensky_ingest.py                                       -> states_all
    # opensky_ingest.py flights_all BEGIN END                 -> BEGIN/END ISO 8601 UTC, e.g. 2026-11-18T00:00:00Z
    # opensky_ingest.py flights_arrival AIRPORT BEGIN END     -> AIRPORT ICAO, e.g. EDDF
    from dtk import make_secret_envar, make_storage_local

    make_secret_envar()
    storage = make_storage_local("./object_storage")

    states_all(storage)
