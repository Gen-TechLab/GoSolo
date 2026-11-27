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

1. W katalogu wybierz **Warszawa → Split** i kliknij **Zarezerwuj**.
2. Na ekranie logowania wybierz rejestrację i utwórz konto klienta. Na potrzeby demonstracji użyj np. adresu `klient@example.com` i hasła `Test1234`.
3. Wróć do oferty, wpisz **2** uczestników i kliknij **Zgłoś rezerwację**. W sekcji **Moje rezerwacje** sprawdź status **Zgłoszona** i cenę **5 800,00 zł**.
4. Wyloguj się i zaloguj jako agent (`agent` / `agent123`). W panelu agenta znajdź zgłoszenie i kliknij **Potwierdź**.
5. W panelu agenta ustaw płatność na **Zaliczka**, wpisz **300,50 zł** i zapisz. Po ponownym uruchomieniu serwera sprawdź na koncie klienta status **Potwierdzona** i pozostałą kwotę **5 499,50 zł**.
6. Wybierz **Anuluj rezerwację** i potwierdź. Miejsca wrócą do katalogu, a zapisana wpłata będzie nadal widoczna w historii rezerwacji.

Domyślne dane agenta służą do uruchomienia lokalnego. Można je zmienić zmiennymi środowiskowymi `AGENT_LOGIN` i `AGENT_PASSWORD`.

### Rozkład lotów

Włącz [AeroDataBox w RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox) i ustaw klucz w zmiennej środowiskowej `AERODATABOX_API_KEY` przed uruchomieniem aplikacji. W PowerShell:

```powershell
$env:AERODATABOX_API_KEY = Read-Host "Klucz RapidAPI"
.\venv\Scripts\python.exe -m src.app
```

W katalogu wpisz miasto lub kod IATA wylotu (np. `KRK`), miasto lub kraj docelowy oraz datę w polu **Wyjazd od**. Rozkład pokazuje do 20 pasujących bezpośrednich lotów z wybranego dnia, z czasami lokalnymi oraz terminalem i bramką, gdy dostawca je podaje. GoSolo przez pięć minut przechowuje w pamięci rozkład danego lotniska i przedziału czasu. Zakres przyszłych dat zależy od planu i pokrycia danych AeroDataBox.

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
