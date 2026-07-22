from cq.countries import Country, load_countries


def test_loads_every_country() -> None:
    assert len(load_countries()) == 195


def test_ids_are_unique() -> None:
    countries = load_countries()
    assert len({c.id for c in countries}) == len(countries)


def test_country_fields_are_parsed() -> None:
    france = next(c for c in load_countries() if c.id == "FRA")
    assert france == Country(
        id="FRA",
        name="France",
        official="French Republic",
        aliases=("French Republic", "République française"),
        capitals=("Paris",),
        region="Europe",
        flag="🇫🇷",
    )


def test_countries_are_hashable() -> None:
    # game.py tracks answered countries in a set, so this has to hold.
    assert len(set(load_countries())) == 195


def test_load_is_cached() -> None:
    assert load_countries() is load_countries()
