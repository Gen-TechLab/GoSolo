"""Checks the data an agent types into the offer form (US03)."""
from datetime import date

TRIP_TYPES = ["plażowy", "aktywny", "miejski"]


def validate_offer(form):
    """Return (data, errors). If errors is empty, data is safe to save."""
    errors = []

    destination = form.get("destination", "").strip()
    start_date = form.get("start_date", "").strip()
    end_date = form.get("end_date", "").strip()
    price = form.get("price", "").strip()
    seats = form.get("seats", "").strip()
    trip_type = form.get("trip_type", "").strip()

    if not destination:
        errors.append("Kierunek jest wymagany.")

    try:
        if date.fromisoformat(end_date) < date.fromisoformat(start_date):
            errors.append("Data powrotu nie może być wcześniejsza niż data wyjazdu.")
    except ValueError:
        errors.append("Podaj poprawne daty wyjazdu i powrotu.")

    try:
        price = float(price)
        if price <= 0:
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
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "price": price,
        "seats": seats,
        "trip_type": trip_type,
    }
    return data, errors
