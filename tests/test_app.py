import db
from validation import validate_offer

GOOD = {"destination": "Grecja - Kreta", "start_date": "2027-08-01", "end_date": "2027-08-08",
        "price": "3200", "seats": "10", "trip_type": "plażowy"}


# US01 - catalog
def test_catalog_shows_offers_from_db(client):
    page = client.get("/").get_data(as_text=True)
    assert "Chorwacja - Split" in page
    assert "plażowy" in page


# US02 - login
def test_login_ok(client):
    r = client.post("/login", data={"login": "agent", "password": "agent123"})
    assert r.status_code == 302 and r.location.endswith("/admin")


def test_login_wrong_shows_error(client):
    r = client.post("/login", data={"login": "agent", "password": "zle"})
    assert "Niepoprawny login lub hasło." in r.get_data(as_text=True)


def test_admin_blocked_when_logged_out(client):
    r = client.get("/admin")
    assert r.status_code == 302 and "/login" in r.location


def test_logout(agent):
    agent.get("/logout")
    assert agent.get("/admin").status_code == 302


# US03 - manage offers
def test_add_offer(agent):
    agent.post("/admin/new", data=GOOD)
    assert any(o["destination"] == "Grecja - Kreta" for o in db.list_offers())


def test_invalid_offer_is_not_saved(agent):
    before = len(db.list_offers())
    r = agent.post("/admin/new", data={**GOOD, "price": "-5"})
    assert "Cena musi być większa od zera." in r.get_data(as_text=True)
    assert len(db.list_offers()) == before


def test_edit_offer(agent):
    agent.post("/admin/1/edit", data={**GOOD, "destination": "Zmieniony"})
    assert db.get_offer(1)["destination"] == "Zmieniony"


def test_delete_offer(agent):
    agent.post("/admin/1/delete")
    assert db.get_offer(1) is None


def test_validation_rules():
    assert validate_offer(GOOD)[1] == []
    assert validate_offer({**GOOD, "destination": ""})[1]
    assert validate_offer({**GOOD, "end_date": "2027-07-01"})[1]  # return before departure
    assert validate_offer({**GOOD, "seats": "0"})[1]
    assert validate_offer({**GOOD, "trip_type": "kosmiczny"})[1]
