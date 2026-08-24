from cq.countries import Country
from cq.game import GuessOutcome, Quiz

FRANCE = Country(
    id="FRA",
    name="France",
    official="French Republic",
    aliases=("French Republic",),
    capitals=("Paris",),
    region="Europe",
    flag="🇫🇷",
)
GERMANY = Country(
    id="DEU",
    name="Germany",
    official="Federal Republic of Germany",
    aliases=(),
    capitals=("Berlin",),
    region="Europe",
    flag="🇩🇪",
)
COUNTRIES = (FRANCE, GERMANY)


def test_correct_guess_scores_once() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0)
    result = quiz.submit("France")
    assert result.outcome == GuessOutcome.CORRECT
    assert result.country == FRANCE
    assert quiz.score == 1


def test_duplicate_guess_does_not_double_count() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0)
    quiz.submit("France")
    result = quiz.submit("france")  # same country, different casing
    assert result.outcome == GuessOutcome.DUPLICATE
    assert quiz.score == 1


def test_unmatched_guess_does_not_change_score() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0)
    result = quiz.submit("Narnia")
    assert result.outcome == GuessOutcome.INCORRECT
    assert result.country is None
    assert quiz.score == 0


def test_is_complete_when_all_answered() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0)
    quiz.submit("France")
    assert not quiz.is_complete(now=1.0)
    quiz.submit("Germany")
    assert quiz.is_complete(now=1.0)


def test_is_complete_when_time_up() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0, duration=10.0)
    assert not quiz.is_complete(now=9.0)
    assert quiz.is_complete(now=10.0)
    assert quiz.is_complete(now=11.0)


def test_remaining_clamps_at_zero() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0, duration=10.0)
    assert quiz.remaining(now=5.0) == 5.0
    assert quiz.remaining(now=999.0) == 0.0


def test_missed_excludes_answered_countries() -> None:
    quiz = Quiz.start(COUNTRIES, now=0.0)
    quiz.submit("France")
    assert quiz.missed() == (GERMANY,)
