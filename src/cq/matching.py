"""Guess normalization and matching against country names/aliases."""

import re
import unicodedata
from collections.abc import Iterable

from cq.countries import Country

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Fold a name or guess down to a comparable form.

    Strips diacritics, lowercases, and collapses everything that isn't a
    letter or digit into single spaces, so "Côte d'Ivoire" and
    "Guinea-Bissau" line up with however a player happens to type them.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _NON_ALNUM.sub(" ", stripped.lower()).strip()


def build_answer_index(countries: Iterable[Country]) -> dict[str, str]:
    """Map every normalized name/official name/alias to its country id."""
    index: dict[str, str] = {}
    for country in countries:
        answers = (country.name, country.official, *country.aliases)
        for answer in answers:
            key = normalize(answer)
            if key:
                index[key] = country.id
    return index


def match(guess: str, index: dict[str, str]) -> str | None:
    """Return the matched country id for a guess, or None."""
    return index.get(normalize(guess))
