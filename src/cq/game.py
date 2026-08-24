"""Pure game rules: score, timer, and the answered set (no I/O)."""

from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cached_property

from cq.countries import Country
from cq.matching import build_answer_index, match

DEFAULT_DURATION = 15 * 60


class GuessOutcome(Enum):
    CORRECT = auto()
    DUPLICATE = auto()
    INCORRECT = auto()


@dataclass(frozen=True, slots=True)
class GuessResult:
    """What happened when a guess was submitted."""

    outcome: GuessOutcome
    country: Country | None


@dataclass
class Quiz:
    """State for a single in-progress (or finished) quiz."""

    countries: tuple[Country, ...]
    index: dict[str, str]
    started_at: float
    duration: float = DEFAULT_DURATION
    answered: set[str] = field(default_factory=set)

    @classmethod
    def start(
        cls,
        countries: tuple[Country, ...],
        now: float,
        duration: float = DEFAULT_DURATION,
    ) -> "Quiz":
        return cls(
            countries=countries,
            index=build_answer_index(countries),
            started_at=now,
            duration=duration,
        )

    @cached_property
    def by_id(self) -> dict[str, Country]:
        """Country lookup by id — `submit` runs on every keystroke."""
        return {country.id: country for country in self.countries}

    def submit(self, guess: str) -> GuessResult:
        country_id = match(guess, self.index)
        if country_id is None:
            return GuessResult(GuessOutcome.INCORRECT, None)

        country = self.by_id[country_id]
        if country_id in self.answered:
            return GuessResult(GuessOutcome.DUPLICATE, country)

        self.answered.add(country_id)
        return GuessResult(GuessOutcome.CORRECT, country)

    def remaining(self, now: float) -> float:
        return max(0.0, self.duration - (now - self.started_at))

    def is_complete(self, now: float) -> bool:
        return self.score == self.total or self.remaining(now) <= 0

    @property
    def score(self) -> int:
        return len(self.answered)

    @property
    def total(self) -> int:
        return len(self.countries)

    def missed(self) -> tuple[Country, ...]:
        return tuple(c for c in self.countries if c.id not in self.answered)

    def region_progress(self) -> tuple[tuple[str, int, int], ...]:
        """(region, found, total) per region, ordered by descending total."""
        totals: dict[str, int] = {}
        found: dict[str, int] = {}
        for country in self.countries:
            totals[country.region] = totals.get(country.region, 0) + 1
            if country.id in self.answered:
                found[country.region] = found.get(country.region, 0) + 1
        return tuple(
            (region, found.get(region, 0), total)
            for region, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
        )
