"""GoSolo - Flask app. Run with:  python app.py"""
import os
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db
from validation import TRIP_TYPES, validate_offer, validate_registration

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# One simple agent account (README: "jedno proste konto agenta").
AGENT_LOGIN = os.environ.get("AGENT_LOGIN", "agent")
AGENT_PASSWORD = os.environ.get("AGENT_PASSWORD", "agent123")


def _is_safe_next_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == "" and parsed.netloc == "" and target.startswith("/") and not target.startswith("//")


def login_required(view):
    """US02: block the admin panel for users who are not logged in as agent."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("agent"):
            flash("Zaloguj się jako agent, aby wejść do panelu agenta.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper

def _normalize_text(value: str) -> str:
    """Normalize Polish letters (ł -> l, diacritics stripped) for case-insensitive search."""
    cleaned = (value or "").replace("ł", "l").replace("Ł", "l")
    decomposed = unicodedata.normalize("NFKD", cleaned)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.casefold().strip()

# ---------- US01: catalog for clients ----------
@app.route("/")
def catalog():
    filters = request.args
    origin = _normalize_text(filters.get("origin", ""))
    destination = _normalize_text(filters.get("destination", ""))
    start = filters.get("start", "")
    end = filters.get("end", "")
    max_price = filters.get("max_price", "").strip()
    try:
        start = date.fromisoformat(start).isoformat() if start else ""
        end = date.fromisoformat(end).isoformat() if end else ""
        price = Decimal(max_price) if max_price else None
        if (start and end and start > end) or (
            price is not None and (not price.is_finite() or price < 0)
        ):
            raise ValueError
    except (ValueError, InvalidOperation):
        return render_template(
            "catalog.html",
            offers=[],
            popular=db.popular_offers(3),
            filters=filters,
            error="Podaj prawidłowy zakres dat i cenę.",
        ), 400

    offers = [
        offer for offer in db.catalog_offers()
        if origin in _normalize_text(offer["origin"] or "")
        and destination in _normalize_text(offer["destination"] or "")
        and (not start or offer["start_date"] >= start)
        and (not end or offer["end_date"] <= end)
        and (price is None or Decimal(str(offer["price"])) <= price)
        and (filters.get("available") != "1" or offer["available_seats"] > 0)
    ]
    return render_template(
        "catalog.html",
        offers=offers,
        popular=db.popular_offers(3),
        filters=filters,
    )


@app.route("/offers/<int:offer_id>/reserve", methods=["GET", "POST"])
def reserve_offer(offer_id):
    offer = db.bookable_offer(offer_id)
    if offer is None:
        abort(404)

    user_id = session.get("user_id")
    is_agent = bool(session.get("agent"))
    if not user_id and not is_agent:
        flash("Zaloguj się lub zarejestruj, aby zarezerwować wycieczkę.")
        return redirect(url_for("login", next=request.path))

    error = None
    if request.method == "POST":
        try:
            participants = int(request.form.get("participants", ""))
        except ValueError:
            participants = 0
        if participants < 1:
            error = "Podaj dodatnią liczbę uczestników."
        else:
            reservation = db.create_reservation(offer_id, participants, user_id=user_id)
            if reservation is not None:
                reservation_id, total = reservation
                flash(f"Zgłoszono rezerwację nr {reservation_id}. "
                      f"Łączna cena: {total // 100},{total % 100:02d} zł.")
                if user_id and not is_agent:
                    return redirect(url_for("my_reservations"))
                return redirect(url_for("catalog"))
            offer = db.bookable_offer(offer_id)
            if offer is None:
                abort(404)
            error = "Brak wystarczającej liczby wolnych miejsc."
    return render_template("reservation_form.html", offer=offer, error=error), 400 if error else 200


@app.route("/my-reservations")
def my_reservations():
    user_id = session.get("user_id")
    if not user_id:
        flash("Zaloguj się, aby zobaczyć swoje rezerwacje.")
        return redirect(url_for("login", next=url_for("my_reservations")))
    return render_template("my_reservations.html", reservations=db.list_user_reservations(user_id))


# ---------- Client registration & login / logout ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    data, errors = {}, []
    if request.method == "POST":
        data, errors = validate_registration(request.form)
        if not errors:
            if db.get_user_by_email(data["email"]) is not None:
                errors.append("Konto z tym adresem e-mail już istnieje.")
            else:
                user_id = db.create_user(data["email"], generate_password_hash(data["password"]))
                if user_id is None:
                    errors.append("Konto z tym adresem e-mail już istnieje.")
                else:
                    session.clear()
                    session["user_id"] = user_id
                    session["user_email"] = data["email"]
                    flash("Konto zostało utworzone. Jesteś zalogowany.")
                    return redirect(url_for("catalog"))
    return render_template("register.html", form_data=data, errors=errors), 400 if errors else 200


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.args.get("next") or request.form.get("next")
    if request.method == "POST":
        identifier = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        if identifier == AGENT_LOGIN and password == AGENT_PASSWORD:
            session.clear()
            session["agent"] = True
            if _is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for("admin"))

        user = db.get_user_by_email(identifier.lower())
        if user is not None and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            flash("Zalogowano pomyślnie.")
            if _is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for("catalog"))

        error = "Niepoprawny login, e-mail lub hasło."
    return render_template("login.html", error=error, next_url=next_url), 400 if error else 200


@app.route("/logout")
def logout():
    session.clear()
    flash("Wylogowano.")
    return redirect(url_for("catalog"))


# ---------- US03: offer management (agent only) ----------
@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", offers=db.list_offers(),
                           reservations=db.list_reservations(),
                           reservation_statuses=RESERVATION_STATUSES,
                           payment_statuses=PAYMENT_STATUSES)


RESERVATION_STATUSES = {
    "pending": "Zgłoszona", "confirmed": "Potwierdzona", "cancelled": "Anulowana",
}
PAYMENT_STATUSES = {"unpaid": "Nieopłacona", "deposit": "Zaliczka", "paid": "Opłacona"}


@app.post("/admin/reservations/<int:reservation_id>/status")
@login_required
def reservation_status(reservation_id):
    status = request.form.get("status")
    if status not in ("confirmed", "cancelled"):
        abort(400)
    if not db.update_reservation_status(reservation_id, status):
        flash("Nie można zmienić statusu tej rezerwacji.")
    return redirect(url_for("admin"))


@app.post("/admin/reservations/<int:reservation_id>/payment")
@login_required
def payment_status(reservation_id):
    status = request.form.get("status")
    if status not in PAYMENT_STATUSES:
        abort(400)
    if not db.update_payment_status(reservation_id, status):
        abort(404)
    return redirect(url_for("admin"))


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def new_offer():
    data, errors = {"origin": "Warszawa"}, []
    if request.method == "POST":
        data, errors = validate_offer(request.form)
        if not errors:
            db.add_offer(data)
            flash("Dodano ofertę.")
            return redirect(url_for("admin"))
    return render_template("offer_form.html", offer=data, errors=errors,
                           trip_types=TRIP_TYPES, title="Nowa oferta")


@app.route("/admin/<int:offer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_offer(offer_id):
    offer = db.get_offer(offer_id)
    if offer is None:
        abort(404)
    data, errors = dict(offer), []
    if request.method == "POST":
        data, errors = validate_offer(request.form)
        if not errors and db.update_offer(offer_id, data):
            flash("Zapisano zmiany.")
            return redirect(url_for("admin"))
        if not errors:
            errors.append("Limit miejsc nie może być mniejszy od liczby zarezerwowanych miejsc.")
    return render_template("offer_form.html", offer=data, errors=errors,
                           trip_types=TRIP_TYPES, title="Edytuj ofertę")


@app.route("/admin/<int:offer_id>/delete", methods=["POST"])
@login_required
def delete_offer(offer_id):
    if db.get_offer(offer_id) is None:
        abort(404)
    if db.delete_offer(offer_id):
        flash("Usunięto ofertę.")
    else:
        flash("Nie można usunąć oferty powiązanej z rezerwacjami.")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)