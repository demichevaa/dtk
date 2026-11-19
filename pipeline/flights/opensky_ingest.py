import sys
from datetime import datetime

from connector import http, opensky
from sdk import FATAL, OBJECT_NAME, OBJECT_STORAGE, SECRET, utc_parse, utc_to_epoch_s


def states_all() -> None:
    token = opensky.token(SECRET["opensky"]["client_id"], SECRET["opensky"]["client_secret"])
    data, meta = http.get(
        f"{opensky.API_URL}/states/all",
        params={"extended": 1},
        headers=opensky.headers(token),
        ok=(200,),
    )
    OBJECT_STORAGE.write_with_meta(OBJECT_NAME("opensky/states_all", meta["fetched_at_utc"]), data, meta)


def flights_all(begin_utc: datetime, end_utc: datetime) -> None:
    """Interval max 2h; previous day or older (OpenSky computes flights nightly)."""
    token = opensky.token(SECRET["opensky"]["client_id"], SECRET["opensky"]["client_secret"])
    data, meta = http.get(
        f"{opensky.API_URL}/flights/all",
        params={"begin": utc_to_epoch_s(begin_utc), "end": utc_to_epoch_s(end_utc)},
        headers=opensky.headers(token),
        ok=(200,),
    )
    OBJECT_STORAGE.write_with_meta(OBJECT_NAME("opensky/flights_all", begin_utc), data, meta)


def flights_arrival(airport_icao: str, begin_utc: datetime, end_utc: datetime) -> None:
    """Interval max 2 days; previous day or older (OpenSky computes flights nightly)."""
    token = opensky.token(SECRET["opensky"]["client_id"], SECRET["opensky"]["client_secret"])
    data, meta = http.get(
        f"{opensky.API_URL}/flights/arrival",
        params={"airport": airport_icao, "begin": utc_to_epoch_s(begin_utc), "end": utc_to_epoch_s(end_utc)},
        headers=opensky.headers(token),
        ok=(200,),
    )
    OBJECT_STORAGE.write_with_meta(OBJECT_NAME(f"opensky/flights_arrival/{airport_icao}", begin_utc), data, meta)


if __name__ == "__main__":
    # opensky_ingest.py                                       -> states_all
    # opensky_ingest.py flights_all BEGIN END                 -> BEGIN/END ISO 8601 UTC, e.g. 2026-11-18T00:00:00Z
    # opensky_ingest.py flights_arrival AIRPORT BEGIN END     -> AIRPORT ICAO, e.g. EDDF
    command, *args = sys.argv[1:] or ["states_all"]
    if command == "states_all":
        states_all()
    elif command == "flights_all":
        flights_all(utc_parse(args[0]), utc_parse(args[1]))
    elif command == "flights_arrival":
        flights_arrival(args[0], utc_parse(args[1]), utc_parse(args[2]))
    else:
        FATAL("Pipeline(%s) unknown", command)
