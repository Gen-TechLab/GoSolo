import unicodedata

from babel import Locale


def normalize_text(value):
    value = (value or "").replace("ł", "l").replace("Ł", "L")
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold().strip()


_TERRITORIES = [Locale.parse(language).territories for language in ("pl", "en", "ru", "uk", "it")]
COUNTRIES = sorted(name for code, name in _TERRITORIES[0].items() if code.isalpha() and len(code) == 2)
COUNTRY_CODES = {
    normalize_text(name): code
    for territories in _TERRITORIES for code, name in territories.items()
    if code.isalpha() and len(code) == 2
}


def destination_matches(query, city, country):
    country = normalize_text(country)
    return (query in normalize_text(city) or query in country
            or (query in COUNTRY_CODES and COUNTRY_CODES[query] == COUNTRY_CODES.get(country)))
