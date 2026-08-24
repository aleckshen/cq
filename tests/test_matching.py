from cq.countries import load_countries
from cq.matching import build_answer_index, match, normalize


def test_normalize_lowercases_and_strips() -> None:
    assert normalize("  United States  ") == "united states"


def test_normalize_strips_diacritics() -> None:
    assert normalize("Côte d'Ivoire") == "cote d ivoire"


def test_normalize_treats_hyphens_as_spaces() -> None:
    assert normalize("Guinea-Bissau") == normalize("Guinea Bissau")


def test_normalize_collapses_punctuation_and_whitespace() -> None:
    assert normalize("U.S.A.") == "u s a"
    assert normalize("Congo,   the") == "congo the"


def test_build_answer_index_has_no_cross_country_collisions() -> None:
    # Non-Latin-script aliases (Cyrillic, Chinese, Armenian, ...) normalize to
    # "" and are intentionally left out of the index, so skip those here.
    countries = load_countries()
    index = build_answer_index(countries)
    for country in countries:
        for answer in (country.name, country.official, *country.aliases):
            key = normalize(answer)
            if key:
                assert index[key] == country.id


def test_match_resolves_name_official_and_alias() -> None:
    index = build_answer_index(load_countries())
    assert match("France", index) == "FRA"
    assert match("French Republic", index) == "FRA"
    assert match("USA", index) == "USA"
    assert match("UAE", index) == "ARE"


def test_match_is_case_and_diacritic_insensitive() -> None:
    index = build_answer_index(load_countries())
    assert match("france", index) == "FRA"
    assert match("cote d'ivoire", index) == "CIV"
    assert match("CÔTE D'IVOIRE", index) == "CIV"


def test_match_returns_none_for_unknown_guess() -> None:
    index = build_answer_index(load_countries())
    assert match("Narnia", index) is None
    assert match("", index) is None
