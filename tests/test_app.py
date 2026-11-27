from src import db
from src.validation import validate_offer, validate_registration

GOOD = {
    "origin": "Warszawa",
    "destination": "Heraklion",
    "country": "Grecja",
    "start_date": "2027-08-01",
    "end_date": "2027-08-08",
    "price": "3200",
    "seats": "10",
    "trip_type": "plażowy",
}


def _register_and_login_client(client, email="klient@example.com", password="Password1"):
    r = client.post(
        "/register",
        data={
            "email": email,
            "password": password,
            "password_confirm": password,
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    return client


# US01 - catalog
def test_catalog_shows_offers_from_db(client):
    page = client.get("/").get_data(as_text=True)
    assert "Warszawa → Split" in page
    assert "plażowy" in page


# US02 - login
def test_login_ok(client):
    r = client.post("/login", data={"login": "agent", "password": "agent123"})
    assert r.status_code == 302 and r.location.endswith("/admin")


def test_login_wrong_shows_error(client):
    r = client.post("/login", data={"login": "agent", "password": "zle"})
    assert "Niepoprawny login, e-mail lub hasło." in r.get_data(as_text=True)


def test_admin_blocked_when_logged_out(client):
    r = client.get("/admin")
    assert r.status_code == 302 and "/login" in r.location


def test_logout(agent):
    agent.get("/logout")
    assert agent.get("/admin").status_code == 302


# Client registration & login
def test_register_and_duplicate_email_blocked(client):
    _register_and_login_client(client, email="test@example.com", password="User123")
    client.get("/logout")
    r = client.post(
        "/register",
        data={
            "email": "test@example.com",
            "password": "User123",
            "password_confirm": "User123",
        },
    )
    assert r.status_code == 400
    assert "Konto z tym adresem e-mail już istnieje." in r.get_data(as_text=True)


def test_registration_password_rules():
    assert validate_registration({
        "email": "a@b.pl",
        "password": "abc",
        "password_confirm": "abc",
    })[1]
    assert validate_registration({
        "email": "a@b.pl",
        "password": "abcdef",
        "password_confirm": "abcdef",
    })[1]
    assert validate_registration({
        "email": "a@b.pl",
        "password": "Password1",
        "password_confirm": "Password2",
    })[1]
    assert validate_registration({
        "email": "a@b.pl",
        "password": "Password1",
        "password_confirm": "Password1",
    })[1] == []


# US03 - manage offers
def test_add_offer(agent):
    agent.post("/admin/new", data=GOOD)
    assert any(o["destination"] == "Heraklion" and o["country"] == "Grecja" for o in db.list_offers())


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
    assert validate_offer({**GOOD, "origin": ""})[1]
    assert validate_offer({**GOOD, "destination": ""})[1]
    assert validate_offer({**GOOD, "end_date": "2027-07-01"})[1]  # return before departure
    assert validate_offer({**GOOD, "seats": "0"})[1]
    assert validate_offer({**GOOD, "trip_type": "kosmiczny"})[1]


def test_catalog_combines_filters(client):
    response = client.get("/", query_string={
        "origin": "KRK",
        "destination": "WLOCHY",
        "start": "2027-04-01",
        "end": "2027-04-30",
        "max_price": "2100",
        "available": "1",
    })
    page = response.get_data(as_text=True)
    catalog_part = page.split('id="catalog-title"', 1)[1]
    assert "Kraków → Rzym" in catalog_part
    assert "Warszawa → Split" not in catalog_part
    assert "Katowice → Poprad" not in catalog_part


def test_catalog_searches_countries_in_supported_languages(client):
    db.add_offer({**GOOD, "destination": "Tokio", "country": "Japonia"})
    for query in ("Italia", "Италия", "Італія", "Italy", "Włochy"):
        page = client.get("/", query_string={"destination": query}).get_data(as_text=True)
        assert "Kraków → Rzym" in page
        assert "Warszawa → Split" not in page
    page = client.get("/", query_string={"destination": "Япония"}).get_data(as_text=True)
    assert "Warszawa → Tokio" in page
    assert "Kraków → Rzym" not in page


def test_reservation_enforces_capacity_and_calculates_total(client):
    _register_and_login_client(client)
    offer = db.get_offer(1)
    path = "/offers/1/reserve"
    assert client.post(path, data={"participants": offer["seats"] + 1}).status_code == 400
    response = client.post(path, data={"participants": offer["seats"]}, follow_redirects=True)
    assert "58000,00 zł" in response.get_data(as_text=True)
    assert client.post(path, data={"participants": 1}).status_code == 400
    assert len(db.list_reservations()) == 1
    assert "Warszawa → Split" not in client.get("/?available=1").get_data(as_text=True)


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


def test_customer_can_cancel_only_own_reservation(client):
    _register_and_login_client(client)
    client.post("/offers/1/reserve", data={"participants": 2})
    mine = db.list_reservations()[0]["id"]
    other_user = db.create_user("other@example.com", "hash")
    other, _ = db.create_reservation(1, 1, user_id=other_user)
    db.update_reservation_status(mine, "confirmed")
    db.update_payment_status(mine, "deposit", 10000)
    page = client.get("/my-reservations").get_data(as_text=True)
    assert "Anuluj rezerwację" in page
    with client.session_transaction() as active_session:
        token = active_session["cancel_token"]
    assert client.get(f"/my-reservations/{mine}/cancel").status_code == 405
    assert client.post(f"/my-reservations/{mine}/cancel").status_code == 400
    assert client.post(f"/my-reservations/{other}/cancel", data={"token": token}).status_code == 404
    for _ in range(2):
        page = client.post(f"/my-reservations/{mine}/cancel", data={"token": token},
                           follow_redirects=True).get_data(as_text=True)
        assert "Anulowana" in page and "Anuluj rezerwację" not in page
    assert db.bookable_offer(1)["available_seats"] == 19
    assert db.list_reservations()[1]["deposit_grosz"] == 10000


def test_agent_records_deposit_and_customer_sees_balance(client):
    _register_and_login_client(client)
    client.post("/offers/1/reserve", data={"participants": 1})
    reservation = db.list_reservations()[0]
    path = f"/admin/reservations/{reservation['id']}/payment"
    agent = client.application.test_client()
    agent.post("/login", data={"login": "agent", "password": "agent123"})
    agent.post(path, data={"status": "deposit", "deposit": "300,50"})
    db.init_db()
    page = client.get("/my-reservations").get_data(as_text=True)
    assert "300,50 zł" in page and "2\u00a0599,50 zł" in page
    agent.post(path, data={"status": "deposit", "deposit": "2900.00"})
    assert db.list_reservations()[0]["deposit_grosz"] == 30050
    agent.post(path, data={"status": "paid"})
    assert db.list_reservations()[0]["deposit_grosz"] is None
    assert "Opłacona" in client.get("/my-reservations").get_data(as_text=True)
