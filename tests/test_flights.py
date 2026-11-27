import io
import json
from collections import OrderedDict
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

from src import flights


def _leg(number, destination, hour="08:35", boarding=False):
    return {
        "number": number,
        "airline": {"name": "Example Air"},
        "status": "Boarding" if boarding else "Expected",
        "departure": {
            "scheduledTime": {"local": f"2027-04-02 {hour}+02:00"},
            "terminal": "1", "gate": "A12",
        },
        "arrival": {
            "airport": {"iata": destination},
            "scheduledTime": {"local": "2027-04-02 10:35+02:00"},
        },
    }


def test_country_city_and_iata_search_reuse_airport_schedule(client, monkeypatch):
    monkeypatch.setenv("AERODATABOX_API_KEY", "fake-local-test-key")
    monkeypatch.setattr(flights, "_cache", OrderedDict())
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        assert timeout == 4
        assert request.get_header("X-rapidapi-key") == "fake-local-test-key"
        response = io.BytesIO(json.dumps({
            "departures": [_leg("FR 123", "FCO", boarding=True),
                           _leg("FR 456", "MXP"), _leg("FR 789", "CDG")],
        }).encode())
        response.status = 200
        return response

    monkeypatch.setattr(flights, "urlopen", fake_urlopen)
    params = {"origin": "KRK", "destination": "Италия", "start": "2027-04-02"}
    page = client.get("/", query_string=params).get_data(as_text=True)
    assert page.count("FR 123") == 1 and "FR 456" in page and "FR 789" not in page
    assert "A12" in page and "08:35" in page and "10:35" in page
    assert "Trwa wejście na pokład" in page and "fake-local-test-key" not in page
    page = client.get("/", query_string={**params, "destination": "Rzym"}).get_data(as_text=True)
    assert "FR 123" in page and "FR 456" not in page
    page = client.get("/", query_string={**params, "destination": "MXP"}).get_data(as_text=True)
    assert "FR 456" in page and "FR 123" not in page
    assert len(calls) == 2
    assert urlsplit(calls[0]).path.endswith("/KRK/2027-04-02T00:00/2027-04-02T12:00")
    assert urlsplit(calls[1]).path.endswith("/KRK/2027-04-02T12:00/2027-04-03T00:00")
    assert parse_qs(urlsplit(calls[0]).query)["withLeg"] == ["true"]


def test_provider_failure_does_not_break_catalog(client, monkeypatch):
    monkeypatch.setenv("AERODATABOX_API_KEY", "fake-local-test-key")
    monkeypatch.setattr(flights, "_cache", OrderedDict())

    def unavailable(*_args, **_kwargs):
        raise URLError("unavailable")

    monkeypatch.setattr(flights, "urlopen", unavailable)
    response = client.get("/", query_string={"origin": "Kraków", "destination": "Włochy", "start": "2027-04-02"})
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Rozkład jest chwilowo niedostępny" in page
    assert "Kraków → Rzym" in page
