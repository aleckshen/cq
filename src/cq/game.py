"""Pure game rules: score, timer, and the answered set (no I/O)."""

from dataclasses import dataclass, field
from enum import Enum, auto

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

    def submit(self, guess: str) -> GuessResult:
        country_id = match(guess, self.index)
        if country_id is None:
            return GuessResult(GuessOutcome.INCORRECT, None)

        country = next(c for c in self.countries if c.id == country_id)
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
