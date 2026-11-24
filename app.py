"""GoSolo - Flask app. Run with:  python app.py"""
import os
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

import db
from validation import TRIP_TYPES, validate_offer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# One simple agent account (README: "jedno proste konto agenta").
AGENT_LOGIN = os.environ.get("AGENT_LOGIN", "agent")
AGENT_PASSWORD = os.environ.get("AGENT_PASSWORD", "agent123")


def login_required(view):
    """US02: block the admin panel for users who are not logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("agent"):
            flash("Zaloguj się, aby wejść do panelu agenta.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ---------- US01: catalog for clients ----------
@app.route("/")
def catalog():
    return render_template("catalog.html", offers=db.list_offers())




# ---------- US02: agent login / logout ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (request.form.get("login") == AGENT_LOGIN
                and request.form.get("password") == AGENT_PASSWORD):
            session["agent"] = True
            return redirect(url_for("admin"))
        error = "Niepoprawny login lub hasło."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("Wylogowano.")
    return redirect(url_for("catalog"))


# ---------- US03: offer management (agent only) ----------
@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", offers=db.list_offers())


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def new_offer():
    data, errors = {}, []
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
        if not errors:
            db.update_offer(offer_id, data)
            flash("Zapisano zmiany.")
            return redirect(url_for("admin"))
    return render_template("offer_form.html", offer=data, errors=errors,
                           trip_types=TRIP_TYPES, title="Edytuj ofertę")


@app.route("/admin/<int:offer_id>/delete", methods=["POST"])
@login_required
def delete_offer(offer_id):
    db.delete_offer(offer_id)
    flash("Usunięto ofertę.")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
