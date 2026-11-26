"""Checks form data for offers (US03) and user registration."""
import re
from datetime import date
from math import isfinite

TRIP_TYPES = ["plażowy", "aktywny", "miejski"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_offer(form):
    """Return (data, errors). If errors is empty, data is safe to save."""
    errors = []

    origin = form.get("origin", "").strip()
    destination = form.get("destination", "").strip()
    start_date = form.get("start_date", "").strip()
    end_date = form.get("end_date", "").strip()
    price = form.get("price", "").strip()
    seats = form.get("seats", "").strip()
    trip_type = form.get("trip_type", "").strip()

    if not origin:
        errors.append("Miejsce wyjazdu (Skąd) jest wymagane.")

    if not destination:
        errors.append("Kierunek (Dokąd) jest wymagany.")

    try:
        if date.fromisoformat(end_date) < date.fromisoformat(start_date):
            errors.append("Data powrotu nie może być wcześniejsza niż data wyjazdu.")
    except ValueError:
        errors.append("Podaj poprawne daty wyjazdu i powrotu.")

    try:
        price = float(price)
        if not isfinite(price) or price <= 0:
            errors.append("Cena musi być większa od zera.")
    except ValueError:
        errors.append("Cena musi być liczbą.")

    try:
        seats = int(seats)
        if seats < 1:
            errors.append("Limit miejsc musi wynosić co najmniej 1.")
    except ValueError:
        errors.append("Limit miejsc musi być liczbą całkowitą.")

    if trip_type not in TRIP_TYPES:
        errors.append("Wybierz typ wyjazdu: plażowy, aktywny lub miejski.")

    data = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "price": price,
        "seats": seats,
        "trip_type": trip_type,
    }
    return data, errors


def validate_registration(form):
    """Validate email, password (min 6 chars, >=1 letter, >=1 digit), and password confirmation."""
    errors = []

    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    password_confirm = form.get("password_confirm", "")

    if not email or not EMAIL_RE.match(email):
        errors.append("Podaj poprawny adres e-mail.")

    has_letter = any(ch.isalpha() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    if len(password) < 6 or not has_letter or not has_digit:
        errors.append("Hasło musi mieć co najmniej 6 znaków oraz zawierać przynajmniej jedną literę i jedną cyfrę.")

    if password != password_confirm:
        errors.append("Hasła nie są identyczne.")

    data = {"email": email, "password": password}
    return data, errors