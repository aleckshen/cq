"""Country data loading and the Country model."""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files


@dataclass(frozen=True, slots=True)
class Country:
    """One guessable country, as stored in data/countries.json."""

    id: str
    name: str
    official: str
    aliases: tuple[str, ...]
    capitals: tuple[str, ...]
    region: str
    flag: str


@cache
def load_countries() -> tuple[Country, ...]:
    """Return every country in the bundled dataset, parsed once per process."""
    # files() rather than __file__ so this keeps working from an installed wheel.
    source = files("cq").joinpath("data/countries.json").read_text(encoding="utf-8")
    return tuple(
        Country(
            id=record["id"],
            name=record["name"],
            official=record["official"],
            aliases=tuple(record["aliases"]),
            capitals=tuple(record["capitals"]),
            region=record["region"],
            flag=record["flag"],
        )
        for record in json.loads(source)
    )
