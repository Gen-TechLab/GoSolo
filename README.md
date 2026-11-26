# GoSolo

Aplikacja Flask i SQLite dla biura podróży. Klient przegląda oferty i zgłasza rezerwacje, a agent je potwierdza lub anuluje. Wymagany Python 3.12 lub nowszy.

## Zespół

- [Rostyslav Volovets](https://github.com/Ros-Gaben) — struktura projektu, baza danych i katalog ofert.
- [Bohdan Moroz](https://github.com/SebastianFarki) — rezerwacje, testy i dokumentacja.

## Uruchomienie i demonstracja

### Uruchomienie w Windows (PowerShell)

W katalogu repozytorium wykonaj:

```powershell
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m src.app
```

### Uruchomienie w macOS i Linux

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m src.app
```

Otwórz <http://127.0.0.1:5000>. Przy pierwszym uruchomieniu aplikacja tworzy plik `gosolo.db` i dodaje przykładowe oferty.

### Ścieżka MVP — od katalogu do potwierdzenia rezerwacji

1. W katalogu wybierz **Chorwacja - Split** i kliknij **Zarezerwuj**.
2. Na ekranie logowania wybierz rejestrację i utwórz konto klienta. Na potrzeby demonstracji użyj np. adresu `klient@example.com` i hasła `Test1234`.
3. Wróć do oferty, wpisz **2** uczestników i kliknij **Zgłoś rezerwację**. W sekcji **Moje rezerwacje** sprawdź status `pending` i cenę **5800,00 zł**.
4. Wyloguj się i zaloguj jako agent (`agent` / `agent123`). W panelu agenta znajdź zgłoszenie i kliknij **Potwierdź**.
5. Zatrzymaj serwer skrótem **Ctrl+C** i uruchom go ponownie tym samym poleceniem. Po zalogowaniu na konto klienta sprawdź, czy w sekcji **Moje rezerwacje** nadal widnieje status `confirmed`.

Domyślne dane agenta służą do uruchomienia lokalnego. Można je zmienić zmiennymi środowiskowymi `AGENT_LOGIN` i `AGENT_PASSWORD`.

Testy uruchom w katalogu repozytorium poleceniem `.\venv\Scripts\python.exe -m pytest` w Windows albo `./venv/bin/python -m pytest` w macOS i Linux.

### Struktura projektu

| Plik lub katalog | Odpowiedzialność |
|---|---|
| `src/app.py` | Interfejs HTTP, sesje i obsługa formularzy |
| `src/db.py` | Schemat SQLite, dane przykładowe, zapis ofert i rezerwacji oraz kontrola dostępności miejsc |
| `src/validation.py` | Reguły walidacji formularzy ofert i rejestracji |
| `src/templates/` i `src/static/` | Szablony HTML i style |
| `tests/` | Testy pytest z odrębną bazą dla każdego testu aplikacji |
| `requirements.txt` i `.gitignore` | Zależności oraz wykluczenia lokalnych plików, w tym `venv/` i bazy |
