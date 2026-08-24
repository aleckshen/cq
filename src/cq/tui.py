"""Textual TUI application."""

import math
import time
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Header, Input, RichLog, Static

from cq.countries import Country, load_countries
from cq.game import DEFAULT_DURATION, GuessOutcome, Quiz

BANNER = r"""
 ██████╗ ██████╗
██╔════╝██╔═══██╗
██║     ██║   ██║
██║     ██║▄▄ ██║
╚██████╗╚██████╔╝
 ╚═════╝ ╚══▀▀═╝
""".strip("\n")

MENU_WIDTH = 46  # content width of the dashboard, minus its padding
MENU_ROW_WIDTH = MENU_WIDTH - 4  # inside the menu panel's border and padding

CQ_THEME = Theme(
    name="cq",
    primary="#7dcfff",
    secondary="#bb9af7",
    accent="#ff9e64",
    success="#9ece6a",
    warning="#e0af68",
    error="#f7768e",
    foreground="#c0caf5",
    background="#16161e",
    surface="#1a1b26",
    panel="#292e42",
    dark=True,
)


@dataclass(frozen=True, slots=True)
class MenuEntry:
    """One row of the landing menu."""

    key: str
    label: str
    countries: tuple[Country, ...]


def menu_entries() -> tuple[MenuEntry, ...]:
    """Built on demand rather than at import time, so `cq --help` doesn't
    read and parse the country dataset."""
    return (
        MenuEntry("world", "the whole world", load_countries()),
        MenuEntry("quit", "quit", ()),
    )


class MenuList(Vertical):
    """A focusable list of menu rows, driven by a pointer rather than a highlight."""

    can_focus = True

    BINDINGS = [
        Binding("up,k", "move(-1)", "Up", show=False),
        Binding("down,j", "move(1)", "Down", show=False),
        Binding("enter,space", "choose", "Start", show=False),
    ]

    index = reactive(0)

    def __init__(self, entries: tuple[MenuEntry, ...]) -> None:
        super().__init__(id="menu")
        self.entries = entries

    class Chosen(Message):
        def __init__(self, entry: MenuEntry) -> None:
            super().__init__()
            self.entry = entry

    def compose(self) -> ComposeResult:
        for position, entry in enumerate(self.entries):
            yield Static(
                self._row(entry, selected=position == 0),
                id=f"row-{position}",
                classes="menu-row" + (" -last" if entry.key == "quit" else ""),
            )

    def _row(self, entry: MenuEntry, *, selected: bool) -> Content:
        count = f"{len(entry.countries)}" if entry.countries else ""
        label = f"{entry.label:<{MENU_ROW_WIDTH - 8}}{count:>6}"
        if selected:
            pointer = Content.styled("❯ ", "$accent")
            return pointer + Content.styled(label, "bold $text")
        return Content.styled("  ") + Content.styled(label, "$text-muted")

    def watch_index(self, index: int) -> None:
        for position, entry in enumerate(self.entries):
            self.query_one(f"#row-{position}", Static).update(
                self._row(entry, selected=position == index)
            )

    def action_move(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.entries)

    def action_choose(self) -> None:
        self.post_message(self.Chosen(self.entries[self.index]))

    def on_click(self) -> None:
        self.focus()


class MenuScreen(Screen[None]):
    """Landing screen: a centered dashboard to pick which quiz to start."""

    BINDINGS = [Binding("q,escape", "quit_app", "Quit")]

    DEFAULT_CSS = f"""
    MenuScreen {{
        align: center middle;
        background: $background;
    }}
    MenuScreen #dashboard {{
        width: {MENU_WIDTH + 4};
        height: auto;
        padding: 0 2;
    }}
    MenuScreen #logo {{
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $primary;
    }}
    MenuScreen #subtitle {{
        width: 100%;
        text-align: center;
        color: $text-muted;
        margin: 1 0 2 0;
    }}
    MenuScreen #menu {{
        width: 100%;
        height: auto;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-muted;
        padding: 1 1;
        &:focus {{
            border: round $primary;
            border-title-color: $primary;
        }}
    }}
    MenuScreen .menu-row {{
        width: 100%;
        height: 1;
    }}
    MenuScreen .menu-row.-last {{
        margin-top: 1;
    }}
    MenuScreen #hint {{
        width: 100%;
        text-align: center;
        color: $text-disabled;
        margin-top: 2;
    }}
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dashboard"):
            yield Static(BANNER, id="logo")
            yield Static("how many countries can you name?", id="subtitle")
            yield MenuList(menu_entries())
            yield Static("↑↓ move   ⏎ start   q quit", id="hint")

    def on_mount(self) -> None:
        menu = self.query_one(MenuList)
        menu.border_title = "quizzes"
        menu.focus()

    def on_menu_list_chosen(self, event: MenuList.Chosen) -> None:
        if event.entry.key == "quit":
            self.app.exit()
            return
        self.app.push_screen(QuizScreen(event.entry.countries))

    def action_quit_app(self) -> None:
        self.app.exit()


class QuizScreen(Screen[None]):
    """A single timed quiz: type guesses, no need to press enter."""

    BINDINGS = [
        Binding("escape", "give_up", "Menu"),
        Binding("ctrl+r", "restart", "Restart"),
    ]

    DEFAULT_CSS = """
    QuizScreen #status {
        height: auto;
        padding: 0 1;
    }
    QuizScreen #status Static {
        width: auto;
        color: $primary;
        text-style: bold;
        margin-right: 2;
    }
    QuizScreen RichLog {
        height: 1fr;
        border: none;
    }
    """

    def __init__(self, countries: tuple[Country, ...], duration: float = DEFAULT_DURATION) -> None:
        super().__init__()
        self.countries = countries
        self.duration = duration
        self.quiz = Quiz.start(countries, now=time.monotonic(), duration=duration)
        self._finished = False

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
        # Round up: a quiz that has just started has 899.99s left, and
        # truncating showed the player 14:59 on a 15:00 quiz.
        remaining = math.ceil(self.quiz.remaining(time.monotonic()))
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

    def action_give_up(self) -> None:
        self.finish()

    def action_restart(self) -> None:
        self._finished = True  # stop this screen's timer from re-entering finish()
        self.app.switch_screen(QuizScreen(self.countries, self.duration))

    def finish(self) -> None:
        # on_tick and on_input_changed can both land on the last country, and
        # switching twice would stack two results screens.
        if self._finished:
            return
        self._finished = True
        self.app.switch_screen(ResultsScreen(self.quiz))


class ResultsScreen(Screen[None]):
    """Final score and the countries that got away."""

    BINDINGS = [Binding("escape,enter", "back_to_menu", "Back to menu")]

    DEFAULT_CSS = """
    ResultsScreen #final-score {
        padding: 1;
        color: $primary;
        text-style: bold;
    }
    """

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

    CSS = """
    Footer {
        background: $surface;
    }
    Footer > .footer-key--key {
        color: $accent;
        background: $surface;
    }
    Footer > .footer-key--description {
        color: $text-muted;
        background: $surface;
    }
    """

    def on_mount(self) -> None:
        self.register_theme(CQ_THEME)
        self.theme = "cq"
        self.push_screen(MenuScreen())
