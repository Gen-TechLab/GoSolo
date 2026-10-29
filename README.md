# GoSolo — karta projektu

Aplikacja internetowa dla biura podróży

## Zespół

- **Nazwa zespołu:** [Gen-TechLab](https://github.com/Gen-TechLab)
- **Rostyslav Volovets** — GitHub: **[Ros-Gaben](https://github.com/Ros-Gaben)**
- **Bohdan Moroz** — GitHub: **[SebastianFarki](https://github.com/SebastianFarki)**
- **Branża:** Biuro Podróży
- **Repozytorium:** <https://github.com/Gen-TechLab/GoSolo>

## Problem i użytkownicy

**Problem.** Małe biuro podróży prowadzi oferty, dane klientów i rezerwacje w arkuszach kalkulacyjnych, e-mailach i notatkach. Prowadzi to do błędów: rezerwacji ponad limit miejsc, gubienia danych klientów, trudności ze znalezieniem pasującej oferty oraz braku szybkiego podglądu, ile miejsc zostało i które rezerwacje są opłacone. Klienci z kolei trudno dobierają wyjazd do swojego nastroju, obawiają się podwyżki ceny w trakcie decyzji i nie wiedzą, co spakować.

**Użytkownicy.**

- **Klient biura** — przegląda ofertę w przeglądarce (na komputerze lub telefonie), dobiera wyjazd do nastroju, zgłasza rezerwację, może zamrozić cenę i korzysta z listy rzeczy do spakowania.
- **Agent biura podróży** (panel zarządzania; w małym biurze także właściciel) — dodaje oferty, obsługuje klientów, potwierdza i anuluje rezerwacje.

Aplikacja działa w przeglądarce i dostosowuje się do ekranu telefonu; osobna aplikacja mobilna nie jest planowana.

## Główne funkcje

1. **Oferty wycieczek** — katalog dla klientów i panel agenta z prostym logowaniem. Oferta ma kierunek, termin, cenę za osobę, limit miejsc, typ wyjazdu (plażowy, aktywny, miejski) i tagi nastroju.
2. **Rezerwacje i klienci** — klient zgłasza rezerwację na stronie (oferta, liczba osób), system sprawdza wolne miejsca i liczy cenę. Agent potwierdza lub anuluje rezerwację i ustawia status płatności (nieopłacona, zaliczka, opłacona).
3. **Dobór wycieczki według nastroju (AI)** — filtry (kierunek, termin, cena, dostępność) oraz opis nastroju własnymi słowami, np. „cichy relaks nad morzem do 3000 zł”. Model językowy (LLM, przez API) wybiera z katalogu biura kilka pasujących ofert i krótko uzasadnia wybór, a aplikacja sprawdza, czy wskazane oferty istnieją w bazie. Gdy API nie działa, oferty są sortowane według tagów nastroju.
4. **Zamrożenie ceny (Price Freeze)** — klient może na 48 godzin zamrozić cenę i zablokować miejsca. Późniejsza zmiana ceny oferty nie dotyczy zamrożonej rezerwacji, a po upływie czasu miejsca wracają do puli.
5. **Asystent pakowania** — dla wybranej wycieczki model językowy tworzy listę rzeczy na podstawie typu wyjazdu, klimatu w terminie podróży (średnie temperatury i opady zapisane dla kierunku) i wskazówek dla kraju, np. stroju w miejscach kultu. Klient odhacza pozycje w aplikacji.

## Zakres MVP

MVP obejmuje funkcje 1–3: katalog z filtrami i doborem według nastroju (model językowy, a przy jego awarii tagi), zgłaszanie rezerwacji oraz panel agenta. Aplikacja działa w przeglądarce (także na telefonie), a dane są trwale zapisywane w bazie SQLite.

MVP uznajemy za gotowe, gdy:

- klient może przeglądać oferty, filtrować je i dobierać według nastroju oraz zgłosić rezerwację, a agent po zalogowaniu zarządza ofertami oraz potwierdza lub anuluje rezerwacje,
- system nie pozwala zarezerwować więcej miejsc, niż zostało w ofercie,
- dane przetrwają restart aplikacji,
- kluczowa logika (wolne miejsca, cena, anulowanie) jest pokryta testami pytest,
- aplikacja jest wdrożona online, a README zawiera adres i instrukcję uruchomienia lokalnego.

Funkcje 4 (zamrożenie ceny) i 5 (asystent pakowania) realizujemy po MVP, w tej kolejności i tylko wtedy, gdy MVP działa i jest przetestowane.

## Poza zakresem

- natywna aplikacja mobilna (strona ma działać na telefonie w przeglądarce) oraz konto klienta z historią zamówień,
- Wiele ról i uprawnień (poza jednym prostym kontem agenta),
- Integracje zewnętrzne (linie lotnicze, hotele, e-mail, SMS, etc),
- generowanie faktur i umów w PDF,
- przechowywanie danych wrażliwych (PESEL, numery paszportów),
- wiele walut i języków oraz pakiety złożone z wielu elementów (lot, hotel, transfer),
- prognoza tłumów w atrakcjach (brak wiarygodnych, darmowych danych) oraz trenowanie własnych modeli.

## Stos technologiczny

- **Język:** Python 3.12 lub nowszy
- **Interfejs:** aplikacja internetowa (backend w Pythonie, HTML i CSS, widok dopasowany do telefonu); framework i hosting wybierzemy w pierwszych tygodniach pracy
- **Baza danych:** SQLite (moduł `sqlite3` z biblioteki standardowej)
- **Sztuczna inteligencja:** model językowy (LLM) wywoływany przez API; dostawcę wybierzemy w pierwszych tygodniach pracy, klucz API trzymamy w zmiennej środowiskowej (poza repozytorium), a w testach model zastępujemy atrapą
- **Testy:** pytest
- **Kontrola wersji:** Git i GitHub (gałęzie, pull requesty, Issues)
- **IDE:** VS Code
- **Środowisko:** `venv` i `requirements.txt`

## Podział ról

- **Rostyslav Volovets — ****Architekt projektu**, **pomysłodawca**** i programista.** Koordynuje wizję i dba o zachowanie ram MVP, odpowiada za strukturę projektu, schemat bazy danych, moduł modelu językowego, funkcje 1 i 3 (po MVP także 5) oraz wdrożenie aplikacji online. Przegląda pull requesty Bohdana.
- **Bohdan Moroz — programista, testy i dokumentacja.** Odpowiada za funkcję 2 (po MVP także 4), konfigurację pytest oraz dokumentację. Przegląda pull requesty Rostyslava.

Zasady współpracy: każda zmiana trafia do głównej gałęzi przez pull request przeglądany przez drugą osobę, każdy pisze testy do własnych modułów, a obie osoby potrafią wyjaśnić cały oddany kod. Dane przykładowe (oferty, klimat i wskazówki dla krajów) przygotowujemy wspólnie.
US01 — Katalog wycieczek

Definition of Done:

- [ ] Klient widzi listę dostępnych wycieczek.
- [ ] Każda oferta zawiera kierunek, termin, cenę, limit miejsc i typ wyjazdu.
- [ ] Dane ofert są pobierane z bazy SQLite.
- [ ] Katalog działa poprawnie na komputerze i telefonie.

US02 — Logowanie agenta

Definition of Done:

- [ ] Agent może zalogować się poprawnym loginem i hasłem.
- [ ] Niepoprawne dane logowania powodują wyświetlenie błędu.
- [ ] Panel administracyjny jest niedostępny dla niezalogowanych użytkowników.
- [ ] Agent może się wylogować.

US03 — Zarządzanie ofertami

Definition of Done:

- [ ] Agent może dodawać nowe oferty wycieczek.
- [ ] Agent może edytować i usuwać istniejące oferty.
- [ ] System sprawdza poprawność wprowadzonych danych.
- [ ] Zmiany są zapisywane w bazie SQLite.

US04 — Filtrowanie wycieczek

Definition of Done:

- [ ] Klient może filtrować wycieczki według kierunku, terminu i ceny.
- [ ] System pozwala wyświetlić tylko oferty z wolnymi miejscami.
- [ ] Można zastosować kilka filtrów jednocześnie.
- [ ] Wyniki odpowiadają wybranym kryteriom.

US05 — Rezerwacja wycieczki

Definition of Done:

- [ ] Klient może wybrać ofertę i liczbę uczestników.
- [ ] System sprawdza dostępność miejsc przed utworzeniem rezerwacji.
- [ ] Całkowita cena jest obliczana poprawnie.
- [ ] Rezerwacja jest zapisywana w SQLite.
- [ ] System blokuje rezerwacje przekraczające limit miejsc.

US06 — Potwierdzanie i anulowanie rezerwacji

Definition of Done:

- [ ] Agent może przeglądać zgłoszone rezerwacje.
- [ ] Agent może potwierdzić lub anulować rezerwację.
- [ ] Status rezerwacji jest aktualizowany w bazie.
- [ ] Anulowanie rezerwacji zwalnia zajęte miejsca.
- [ ] Logika anulowania przechodzi testy pytest.

US07 — Status płatności

Definition of Done:

- [ ] Agent może ustawić status: nieopłacona, zaliczka lub opłacona.
- [ ] Status płatności jest widoczny w panelu agenta.
- [ ] Zmiany statusu są zapisywane w SQLite.
- [ ] Status pozostaje poprawny po ponownym uruchomieniu aplikacji.

US08 — Dobór wycieczki przez AI

Definition of Done:

- [ ] Klient może opisać preferowany wyjazd własnymi słowami.
- [ ] Aplikacja przesyła zapytanie do modelu AI przez API.
- [ ] AI proponuje wycieczki istniejące w katalogu.
- [ ] Każda propozycja zawiera krótkie uzasadnienie.
- [ ] Klucz API nie jest przechowywany w repozytorium.

US09 — Wyszukiwanie według tagów

Definition of Done:

- [ ] Każda oferta może posiadać tagi opisujące nastrój wyjazdu.
- [ ] Gdy API AI jest niedostępne, system automatycznie korzysta z tagów.
- [ ] Wyniki zawierają wyłącznie istniejące oferty.
- [ ] Mechanizm awaryjny działa poprawnie w testach.

US10 — Zamrożenie ceny na 48 godzin

Definition of Done:

- [ ] Klient może zamrozić cenę wycieczki na 48 godzin.
- [ ] Cena rezerwacji nie zmienia się podczas okresu zamrożenia.
- [ ] System blokuje odpowiednią liczbę miejsc.
- [ ] Po upływie 48 godzin niewykorzystana blokada wygasa, a miejsca zostają zwolnione.
- [ ] Mechanizm jest sprawdzony testami pytest.

US11 — Asystent pakowania

Definition of Done:

- [ ] System generuje listę rzeczy do spakowania dla wybranej wycieczki.
- [ ] Lista uwzględnia typ wyjazdu, klimat i wskazówki dotyczące kraju.
- [ ] Klient może zaznaczać spakowane przedmioty.
- [ ] Lista jest czytelna na komputerze i telefonie.
- [ ] Funkcja działa poprawnie dla przykładowych wycieczek.