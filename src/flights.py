"""Read scheduled departures from AeroDataBox via RapidAPI."""
import json
from collections import OrderedDict
from datetime import date, datetime, timedelta
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import airportsdata

from .locations import COUNTRY_CODES, normalize_text


_HOST = "aerodatabox.p.rapidapi.com"
_AIRPORTS = airportsdata.load("IATA")
_CITY_NAMES = {
    "warszawa": "warsaw", "rzym": "rome", "mediolan": "milan", "paryz": "paris",
    "londyn": "london", "wieden": "vienna", "praga": "prague", "ateny": "athens",
    "lizbona": "lisbon", "bruksela": "brussels", "wenecja": "venice",
}
_CACHE_SECONDS = 300
_CACHE_LIMIT = 128
_cache = OrderedDict()
_cache_lock = Lock()


class ScheduleUnavailable(Exception):
    pass


def _city(value):
    value = normalize_text(value)
    return _CITY_NAMES.get(value, value)


def _origin_airports(query):
    if query.upper() in _AIRPORTS:
        return [query.upper()]
    city = _city(query)
    # The airport reference lists Modlin independently of Warsaw.
    if city == "warsaw":
        return ["WAW", "WMI"]
    return [iata for iata, airport in _AIRPORTS.items() if normalize_text(airport["city"]) == city]


def origin_matches(query, city):
    """Match an offer's departure city by name or airport code."""
    normalized_city = normalize_text(city)
    if query in normalized_city:
        return True
    airport = _AIRPORTS.get(query.upper())
    return bool(airport and (_city(airport["city"]) == _city(city)
                             or (query == "wmi" and _city(city) == "warsaw")))


def _fetch_departures(code, start, end, api_key):
    query = urlencode({
        "direction": "Departure", "withLeg": "true",
        "withCancelled": "false", "withCodeshared": "false",
    })
    request = Request(f"https://{_HOST}/flights/airports/iata/{code}/{start}/{end}?{query}")
    request.add_unredirected_header("X-RapidAPI-Key", api_key)
    request.add_unredirected_header("X-RapidAPI-Host", _HOST)
    request.add_header("Accept", "application/json")
    try:
        with urlopen(request, timeout=4) as response:
            data = json.load(response) if response.status != 204 else {}
        departures = data.get("departures") if isinstance(data, dict) else None
        if departures is None and isinstance(data, dict):
            return []
        if not isinstance(departures, list):
            raise ScheduleUnavailable
        return departures
    except HTTPError as exc:
        if exc.code == 404:
            return []
        raise ScheduleUnavailable from exc
    except (OSError, ValueError, URLError) as exc:
        raise ScheduleUnavailable from exc


def _departures(code, start, end, api_key):
    key = (code, start, end)
    with _cache_lock:
        now = monotonic()
        if key in _cache:
            expires, flights = _cache[key]
            if expires > now:
                _cache.move_to_end(key)
                return flights
            del _cache[key]
        flights = _fetch_departures(code, start, end, api_key)
        _cache[key] = (monotonic() + _CACHE_SECONDS, flights)
        if len(_cache) > _CACHE_LIMIT:
            _cache.popitem(last=False)
        return flights


def _schedule_time(movement):
    local = (movement.get("scheduledTime") or {}).get("local")
    try:
        return datetime.fromisoformat(local)
    except (TypeError, ValueError):
        return None


def _flight_row(flight, origin, query, day):
    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}
    airport = arrival.get("airport") or {}
    code = airport.get("iata")
    reference = _AIRPORTS.get(code, {})
    destination = reference.get("city") or airport.get("municipalityName") or airport.get("name")
    if not destination:
        return None
    if query in COUNTRY_CODES:
        if (reference.get("country") or airport.get("countryCode")) != COUNTRY_CODES[query]:
            return None
    elif query.upper() != code and _city(query) not in normalize_text(destination):
        return None

    takeoff = _schedule_time(departure)
    if takeoff is None or takeoff.date() != day:
        return None
    landing = _schedule_time(arrival)
    return {
        "number": flight.get("number"),
        "airline": (flight.get("airline") or {}).get("name"),
        "origin": _AIRPORTS[origin]["city"],
        "origin_code": origin,
        "destination": destination,
        "destination_code": code,
        "departure": takeoff.isoformat(timespec="minutes"),
        "departure_time": takeoff.strftime("%H:%M"),
        "arrival_date": landing.date().isoformat() if landing else None,
        "arrival_time": landing.strftime("%H:%M") if landing else None,
        "terminal": departure.get("terminal"),
        "gate": departure.get("gate"),
        "boarding": flight.get("status") == "Boarding",
    }


def search_flights(origin, destination, departure_day, api_key):
    if not api_key:
        return "unconfigured", []
    if not (origin and destination and departure_day):
        return "idle", []
    airports = _origin_airports(origin)
    if not airports or len(airports) > 2:
        return "choose_airport", []
    day = date.fromisoformat(departure_day)
    if day == date.max:
        return "unavailable", []
    next_day = day + timedelta(days=1)
    windows = ((f"{day}T00:00", f"{day}T12:00"), (f"{day}T12:00", f"{next_day}T00:00"))
    rows = {}
    failed = False
    for airport in airports:
        for start, end in windows:
            try:
                departures = _departures(airport, start, end, api_key)
            except ScheduleUnavailable:
                failed = True
                continue
            for flight in departures:
                row = _flight_row(flight, airport, destination, day)
                if row is None:
                    continue
                key = (airport, row["destination_code"], row["number"], row["departure"])
                rows[key] = row
    results = sorted(rows.values(), key=lambda row: row["departure"])[:20]
    return ("partial" if results else "unavailable") if failed else "ready", results
