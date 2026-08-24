"""Textual TUI application."""

import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, OptionList, RichLog, Static

from cq.countries import Country, load_countries
from cq.game import DEFAULT_DURATION, GuessOutcome, Quiz

# (menu label, countries for that quiz) — add region entries here post-MVP.
MENU_OPTIONS: tuple[tuple[str, tuple[Country, ...]], ...] = (
    ("All Countries — World", load_countries()),
)


class MenuScreen(Screen[None]):
    """Landing screen: pick which quiz to start."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(*(label for label, _ in MENU_OPTIONS))
        yield Footer()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        _, countries = MENU_OPTIONS[event.option_index]
        self.app.push_screen(QuizScreen(countries))


class QuizScreen(Screen[None]):
    """A single timed quiz: type guesses, no need to press enter."""

    DEFAULT_CSS = """
    QuizScreen #status {
        height: auto;
        padding: 0 1;
    }
    QuizScreen #status Static {
        width: auto;
    }
    QuizScreen RichLog {
        height: 1fr;
    }
    """

    def __init__(self, countries: tuple[Country, ...], duration: float = DEFAULT_DURATION) -> None:
        super().__init__()
        self.countries = countries
        self.duration = duration
        self.quiz = Quiz.start(countries, now=time.monotonic(), duration=duration)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="status"):
            yield Static(id="timer")
            yield Static(id="score")
        yield RichLog(id="guessed", auto_scroll=True)
        yield Input(placeholder="Type a country...")
        yield Footer()

    def on_mount(self) -> None:
        self.update_status()
        self.set_interval(1.0, self.on_tick)
        self.query_one(Input).focus()

    def on_tick(self) -> None:
        self.update_status()
        if self.quiz.is_complete(time.monotonic()):
            self.finish()

    def update_status(self) -> None:
        remaining = int(self.quiz.remaining(time.monotonic()))
        minutes, seconds = divmod(remaining, 60)
        self.query_one("#timer", Static).update(f"⏱ {minutes:02d}:{seconds:02d}")
        self.query_one("#score", Static).update(
            f"Score: {self.quiz.score}/{self.quiz.total}"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        result = self.quiz.submit(event.value)
        if result.outcome is GuessOutcome.INCORRECT:
            return

        self.query_one(Input).value = ""
        if result.outcome is GuessOutcome.CORRECT and result.country is not None:
            country = result.country
            self.query_one("#guessed", RichLog).write(f"{country.flag} {country.name}")
            self.update_status()
            if self.quiz.is_complete(time.monotonic()):
                self.finish()

    def finish(self) -> None:
        self.app.switch_screen(ResultsScreen(self.quiz))


class ResultsScreen(Screen[None]):
    """Final score and the countries that got away."""

    BINDINGS = [Binding("escape,enter", "back_to_menu", "Back to menu")]

    def __init__(self, quiz: Quiz) -> None:
        super().__init__()
        self.quiz = quiz

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Final score: {self.quiz.score}/{self.quiz.total}", id="final-score")
        missed = self.quiz.missed()
        if missed:
            yield Static("Missed:")
            log = RichLog(id="missed")
            for country in missed:
                log.write(f"{country.flag} {country.name}")
            yield log
        yield Footer()

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()


class CqApp(App[None]):
    """The cq terminal country-guessing game."""

    TITLE = "cq"

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
