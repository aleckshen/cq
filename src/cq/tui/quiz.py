"""A single timed quiz: type guesses, no need to press enter."""

import time

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Digits, Footer, Input, Static

from cq.countries import Country
from cq.game import DEFAULT_DURATION, GuessOutcome, GuessResult, Quiz
from cq.tui.theme import COUNT_WIDTH, NARROW_WIDTH, SIDEBAR_WIDTH, TIMER_WIDTH
from cq.tui.widgets import CountryColumns, ProgressTile, RegionPanel, clock


class PauseScreen(ModalScreen[bool]):
    """Shown when a running quiz is interrupted: the clock is held while the
    player chooses to resume or give up. Dismisses True to give up."""

    BINDINGS = [
        Binding("escape,enter,r", "resume", "Resume"),
        Binding("g", "give_up", "Give up"),
    ]

    DEFAULT_CSS = """
    PauseScreen {
        align: center middle;
    }
    PauseScreen #box {
        width: 40;
        height: auto;
        padding: 1 2;
        border: round white;
        background: $surface;
    }
    PauseScreen Static {
        width: 100%;
        text-align: center;
    }
    PauseScreen #title {
        text-style: bold;
    }
    PauseScreen #hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("paused", id="title")
            yield Static("the clock is on hold")
            yield Static("r  resume        g  give up", id="hint")
        yield Footer()

    def action_resume(self) -> None:
        self.dismiss(False)

    def action_give_up(self) -> None:
        self.dismiss(True)


class QuizScreen(Screen[None]):
    """A single timed quiz: type guesses, no need to press enter."""

    BINDINGS = [
        Binding("escape", "pause", "Pause"),
        Binding("ctrl+r", "restart", "Restart"),
    ]

    DEFAULT_CSS = f"""
    QuizScreen {{
        background: $background;
    }}
    QuizScreen #hud {{
        height: 5;
        padding: 0 1;
    }}
    QuizScreen .tile {{
        height: 5;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 0 1;
        content-align: center middle;
    }}
    QuizScreen #timer {{
        width: {TIMER_WIDTH};
        text-align: center;
        color: white;
    }}
    QuizScreen #timer.-warn {{
        color: white;
        border: round $warning 40%;
    }}
    QuizScreen #timer.-danger {{
        color: white;
        border: round $error;
    }}
    QuizScreen #score {{
        width: {COUNT_WIDTH};
        text-align: center;
        color: white;
    }}
    QuizScreen #progress {{
        width: 1fr;
        color: $text;
    }}
    QuizScreen #board {{
        height: 1fr;
        padding: 0 1;
    }}
    QuizScreen #found {{
        width: 1fr;
        height: 100%;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }}
    QuizScreen #found-grid {{
        width: 100%;
        height: auto;
    }}
    QuizScreen #empty-hint {{
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: $text-disabled;
    }}
    QuizScreen #regions {{
        width: {SIDEBAR_WIDTH};
        height: 100%;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 1 1 0 1;
        margin-left: 1;
    }}
    QuizScreen.-narrow #regions {{
        display: none;
    }}
    QuizScreen #entry {{
        height: 3;
        padding: 0 1;
    }}
    QuizScreen Input {{
        border: round $panel;
        background: $surface;
        padding: 0 1;
        &:focus {{
            border: round white;
        }}
    }}
    QuizScreen Input.-hit {{
        border: round $success;
    }}
    QuizScreen #message {{
        height: 1;
        padding: 0 3;
        color: $text-disabled;
    }}
    """

    def __init__(
        self,
        countries: tuple[Country, ...],
        duration: float = DEFAULT_DURATION,
        title: str = "quiz",
    ) -> None:
        super().__init__()
        self.countries = countries
        self.duration = duration
        self.quiz_title = title
        self.quiz = Quiz.start(countries, now=time.monotonic(), duration=duration)
        self._finished = False
        self._flash_timer: Timer | None = None
        self._tick: Timer | None = None
        self._paused_at: float | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="hud"):
            yield Digits(clock(self.duration), id="timer", classes="tile")
            yield Digits("0", id="score", classes="tile")
            yield ProgressTile(id="progress", classes="tile")
        with Horizontal(id="board"):
            with VerticalScroll(id="found"):
                yield Static("nothing found yet — start typing", id="empty-hint")
                yield CountryColumns(id="found-grid")
            yield RegionPanel(id="regions")
        with Vertical(id="entry"):
            yield Input(placeholder="type a country…")
        yield Static("", id="message")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#timer").border_title = "time left"
        self.query_one("#score").border_title = "found"
        self.query_one("#progress").border_title = self.quiz_title
        self.query_one("#found").border_title = "your countries"
        self.query_one("#regions").border_title = "regions"
        self.query_one("#found-grid").display = False
        self.update_status()
        self._tick = self.set_interval(0.25, self.on_tick)
        self.query_one(Input).focus()

    def on_resize(self) -> None:
        self.set_class(self.size.width < NARROW_WIDTH, "-narrow")
        self.query_one(RegionPanel).show(self.quiz.region_progress())
        self.query_one(CountryColumns).refresh(layout=True)

    def on_tick(self) -> None:
        self.update_status()
        if self.quiz.is_complete(time.monotonic()):
            self.finish()

    def update_status(self) -> None:
        remaining = self.quiz.remaining(time.monotonic())
        timer = self.query_one("#timer", Digits)
        timer.update(clock(remaining))
        timer.set_class(15 <= remaining < 60, "-warn")
        timer.set_class(remaining < 15, "-danger")

        self.query_one("#score", Digits).update(str(self.quiz.score))
        progress = self.query_one(ProgressTile)
        progress.done = self.quiz.score
        progress.total = self.quiz.total

    def on_input_changed(self, event: Input.Changed) -> None:
        self._apply_guess(self.quiz.submit(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Enter means "done with this one" — resolve it and clear the box.
        self._apply_guess(self.quiz.submit(event.value))
        self.query_one(Input).value = ""

    def _apply_guess(self, result: GuessResult) -> None:
        """React to a guess. Only a fresh match touches the box: it's added
        to the board and the field clears for the next country. Re-typing a
        country already found does nothing — the text is left in place, so a
        short name like "niger" doesn't swallow the "nigeria" you're working
        toward (type it once to claim Niger, then keep going).
        """
        if result.outcome is not GuessOutcome.CORRECT or result.country is None:
            return

        country = result.country
        self.query_one(Input).value = ""
        self.record()
        self.flash("-hit", f"✓  {country.flag} {country.name}")
        self.update_status()
        if self.quiz.is_complete(time.monotonic()):
            self.finish()

    def record(self) -> None:
        """Refresh the found-country list and the region sidebar."""
        grid = self.query_one("#found-grid", CountryColumns)
        if not grid.display:
            self.query_one("#empty-hint").remove()
            grid.display = True
        grid.set_countries(
            c for c in self.quiz.countries if c.id in self.quiz.answered
        )
        self.query_one(RegionPanel).show(self.quiz.region_progress())

    def flash(self, style: str, message: str) -> None:
        """Tint the input border and echo the guess for a beat."""
        entry = self.query_one(Input)
        entry.remove_class("-hit")
        entry.add_class(style)
        self.query_one("#message", Static).update(message)
        if self._flash_timer is not None:
            self._flash_timer.stop()
        self._flash_timer = self.set_timer(0.6, self.clear_flash)

    def clear_flash(self) -> None:
        self.query_one(Input).remove_class("-hit")

    def action_pause(self) -> None:
        """Hold the clock and ask whether to give up or carry on."""
        if self._finished:
            return
        self._paused_at = time.monotonic()
        if self._tick is not None:
            self._tick.pause()
        self.app.push_screen(PauseScreen(), self._after_pause)

    def _after_pause(self, give_up: bool | None) -> None:
        if give_up:
            self.finish()
            return
        if self._paused_at is not None:
            self.quiz.started_at += time.monotonic() - self._paused_at
            self._paused_at = None
        if self._tick is not None:
            self._tick.resume()
        self.update_status()
        self.query_one(Input).focus()

    def action_restart(self) -> None:
        self._finished = True  # stop this screen's timer from re-entering finish()
        self.app.switch_screen(
            QuizScreen(self.countries, self.duration, title=self.quiz_title)
        )

    def finish(self) -> None:
        from cq.tui.results import ResultsScreen

        # on_tick and on_input_changed can both land on the last country, and
        # switching twice would stack two results screens.
        if self._finished:
            return
        self._finished = True
        self.app.switch_screen(ResultsScreen(self.quiz, title=self.quiz_title))
