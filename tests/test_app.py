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


def test_catalog_combines_filters(client):
    response = client.get("/", query_string={
        "destination": "WŁOCHY", "start": "2027-04-01", "end": "2027-04-30",
        "max_price": "2100", "available": "1",
    })
    page = response.get_data(as_text=True)
    assert "Włochy - Rzym" in page
    assert "Chorwacja - Split" not in page
    assert "Słowacja - Tatry" not in page


def test_reservation_enforces_capacity_and_calculates_total(client):
    offer = db.get_offer(1)
    path = "/offers/1/reserve"
    assert client.post(path, data={"participants": offer["seats"] + 1}).status_code == 400
    response = client.post(path, data={"participants": offer["seats"]}, follow_redirects=True)
    assert "58000,00 zł" in response.get_data(as_text=True)
    assert client.post(path, data={"participants": 1}).status_code == 400
    assert len(db.list_reservations()) == 1
    assert "Chorwacja - Split" not in client.get("/?available=1").get_data(as_text=True)


def test_cancellation_releases_seats_once(agent):
    reservation_id, _ = db.create_reservation(1, 20)
    path = f"/admin/reservations/{reservation_id}/status"
    agent.post(path, data={"status": "confirmed"})
    assert db.list_reservations()[0]["status"] == "confirmed"
    assert db.bookable_offer(1)["available_seats"] == 0
    agent.post(path, data={"status": "cancelled"})
    assert db.list_reservations()[0]["status"] == "cancelled"
    assert db.bookable_offer(1)["available_seats"] == 20
    agent.post(path, data={"status": "cancelled"})
    agent.post(path, data={"status": "confirmed"})
    assert db.bookable_offer(1)["available_seats"] == 20


def test_payment_status_persists(agent):
    reservation_id, _ = db.create_reservation(1, 1)
    path = f"/admin/reservations/{reservation_id}/payment"
    assert agent.post(path, data={"status": "invalid"}).status_code == 400
    assert db.list_reservations()[0]["payment_status"] == "unpaid"
    assert agent.post(path, data={"status": "deposit"}).status_code == 302
    db.init_db()
    assert db.list_reservations()[0]["payment_status"] == "deposit"
    page = agent.get("/admin").get_data(as_text=True)
    assert 'value="deposit" selected' in page
