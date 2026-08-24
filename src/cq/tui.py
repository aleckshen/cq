"""Textual TUI application."""

import math
import time
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ItemGrid, Vertical, VerticalScroll
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.theme import Theme
from textual.timer import Timer
from textual.widgets import Digits, Footer, Input, Label, Static

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
NARROW_WIDTH = 92  # below this the quiz hides its region sidebar
SIDEBAR_WIDTH = 28
COLUMN_WIDTH = 24  # min width of a found-country cell before the grid reflows
TIMER_WIDTH = 19  # "15:00" in 3x3 digits, plus the tile's padding and border
COUNT_WIDTH = 14  # three 3x3 digits, plus the tile's padding and border

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


def track(done: int, total: int, width: int) -> Content:
    """A solid two-tone progress track, `width` cells wide."""
    width = max(width, 1)
    filled = 0 if total <= 0 else round(width * done / total)
    filled = max(0, min(width, filled))
    return Content.styled("█" * filled, "$success") + Content.styled(
        "█" * (width - filled), "$panel"
    )


def clock(seconds: float) -> str:
    """Round *up* so a fresh 15:00 quiz reads 15:00, not 14:59."""
    total = max(0, math.ceil(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


@dataclass(frozen=True, slots=True)
class MenuEntry:
    """One row of the landing menu."""

    key: str
    label: str
    countries: tuple[Country, ...]


def menu_entries() -> tuple[MenuEntry, ...]:
    """Built on demand rather than at import time, so `cq --help` doesn't
    read and parse the country dataset."""
    countries = load_countries()
    regions = sorted({country.region for country in countries})
    return (
        MenuEntry("world", "the whole world", countries),
        *(
            MenuEntry(
                region.lower(),
                region.lower(),
                tuple(c for c in countries if c.region == region),
            )
            for region in regions
        ),
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
        self.app.push_screen(QuizScreen(event.entry.countries, title=event.entry.label))

    def action_quit_app(self) -> None:
        self.app.exit()


class ProgressTile(Static):
    """The `n found / n to go` tile, redrawn on resize as well as on score."""

    done = reactive(0)
    total = reactive(0)

    def render(self) -> Content:
        width = max(self.content_size.width, 8)
        percent = 0 if self.total == 0 else round(100 * self.done / self.total)
        caption = f"{self.done} of {self.total} · {self.total - self.done} to go"
        return Content("\n").join(
            (
                track(self.done, self.total, width),
                Content.styled(f"{percent}%".center(width), "bold $success"),
                Content.styled(caption.center(width), "$text-muted"),
            )
        )


class RegionPanel(Static):
    """Sidebar showing how much of each region has been found."""

    def show(self, progress: tuple[tuple[str, int, int], ...]) -> None:
        width = max(self.content_size.width, 8)
        lines: list[Content] = []
        for region, found, total in progress:
            head = f"{region.lower():<{max(width - 8, 1)}}{found:>3}/{total:<3}"
            lines.append(Content.styled(head, "$text-muted"))
            lines.append(track(found, total, width))
            lines.append(Content(""))
        self.update(Content("\n").join(lines))


class QuizScreen(Screen[None]):
    """A single timed quiz: type guesses, no need to press enter."""

    BINDINGS = [
        Binding("escape", "give_up", "Menu"),
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
        color: $primary;
    }}
    QuizScreen #timer.-warn {{
        color: $warning;
        border: round $warning 40%;
    }}
    QuizScreen #timer.-danger {{
        color: $error;
        border: round $error;
    }}
    QuizScreen #score {{
        width: {COUNT_WIDTH};
        text-align: center;
        color: $success;
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
        grid-gutter: 0 1;
    }}
    QuizScreen .found-item {{
        width: 100%;
        height: 1;
        text-wrap: nowrap;
        text-overflow: ellipsis;
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
            border: round $primary;
        }}
    }}
    QuizScreen Input.-hit {{
        border: round $success;
    }}
    QuizScreen Input.-dupe {{
        border: round $warning;
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

    def compose(self) -> ComposeResult:
        with Horizontal(id="hud"):
            yield Digits(clock(self.duration), id="timer", classes="tile")
            yield Digits("0", id="score", classes="tile")
            yield ProgressTile(id="progress", classes="tile")
        with Horizontal(id="board"):
            with VerticalScroll(id="found"):
                yield Static("nothing found yet — start typing", id="empty-hint")
                yield ItemGrid(id="found-grid", min_column_width=COLUMN_WIDTH)
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
        self.set_interval(0.25, self.on_tick)
        self.query_one(Input).focus()

    def on_resize(self) -> None:
        self.set_class(self.size.width < NARROW_WIDTH, "-narrow")
        self.query_one(RegionPanel).show(self.quiz.region_progress())

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
        result = self.quiz.submit(event.value)
        if result.outcome is GuessOutcome.INCORRECT or result.country is None:
            return

        self.query_one(Input).value = ""
        country = result.country
        if result.outcome is GuessOutcome.DUPLICATE:
            self.flash("-dupe", f"already found  {country.flag} {country.name}")
            return

        self.record(country)
        self.flash("-hit", f"✓  {country.flag} {country.name}")
        self.update_status()
        if self.quiz.is_complete(time.monotonic()):
            self.finish()

    def record(self, country: Country) -> None:
        """Add a freshly found country to the grid and the region sidebar."""
        grid = self.query_one("#found-grid", ItemGrid)
        if not grid.display:
            self.query_one("#empty-hint").remove()
            grid.display = True
        grid.mount(
            Label(
                Content.styled(f"{country.flag} {country.name}", "$text"),
                classes="found-item",
            )
        )
        self.query_one("#found", VerticalScroll).scroll_end(animate=False)
        self.query_one(RegionPanel).show(self.quiz.region_progress())

    def flash(self, style: str, message: str) -> None:
        """Tint the input border and echo the guess for a beat."""
        entry = self.query_one(Input)
        entry.remove_class("-hit", "-dupe")
        entry.add_class(style)
        self.query_one("#message", Static).update(message)
        if self._flash_timer is not None:
            self._flash_timer.stop()
        self._flash_timer = self.set_timer(0.6, self.clear_flash)

    def clear_flash(self) -> None:
        self.query_one(Input).remove_class("-hit", "-dupe")

    def action_give_up(self) -> None:
        self.finish()

    def action_restart(self) -> None:
        self._finished = True  # stop this screen's timer from re-entering finish()
        self.app.switch_screen(
            QuizScreen(self.countries, self.duration, title=self.quiz_title)
        )

    def finish(self) -> None:
        # on_tick and on_input_changed can both land on the last country, and
        # switching twice would stack two results screens.
        if self._finished:
            return
        self._finished = True
        self.app.switch_screen(ResultsScreen(self.quiz, title=self.quiz_title))


class ResultsScreen(Screen[None]):
    """Final score, region breakdown, and the countries that got away."""

    BINDINGS = [
        Binding("escape,enter", "back_to_menu", "Menu"),
        Binding("r", "replay", "Replay"),
    ]

    DEFAULT_CSS = f"""
    ResultsScreen {{
        background: $background;
    }}
    ResultsScreen #summary {{
        height: 5;
        padding: 0 1;
    }}
    ResultsScreen .tile {{
        height: 5;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 0 1;
        content-align: center middle;
    }}
    ResultsScreen #final-score {{
        width: {COUNT_WIDTH};
        text-align: center;
        color: $success;
    }}
    ResultsScreen #final-percent {{
        width: {COUNT_WIDTH};
        text-align: center;
        color: $primary;
    }}
    ResultsScreen #final-progress {{
        width: 1fr;
    }}
    ResultsScreen #results-board {{
        height: 1fr;
        padding: 0 1;
    }}
    ResultsScreen #missed {{
        width: 1fr;
        height: 100%;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }}
    ResultsScreen #missed-grid {{
        width: 100%;
        height: auto;
        grid-gutter: 0 1;
    }}
    ResultsScreen .missed-item {{
        width: 100%;
        height: 1;
        color: $text-muted;
        text-wrap: nowrap;
        text-overflow: ellipsis;
    }}
    ResultsScreen #perfect {{
        width: 1fr;
        height: 100%;
        border: round $success;
        border-title-align: left;
        border-title-color: $success;
        content-align: center middle;
        color: $success;
        text-style: bold;
    }}
    ResultsScreen #breakdown {{
        width: {SIDEBAR_WIDTH};
        height: 100%;
        border: round $panel;
        border-title-align: left;
        border-title-color: $text-disabled;
        padding: 1 1 0 1;
        margin-left: 1;
    }}
    ResultsScreen.-narrow #breakdown {{
        display: none;
    }}
    """

    def __init__(self, quiz: Quiz, title: str = "quiz") -> None:
        super().__init__()
        self.quiz = quiz
        self.quiz_title = title

    def compose(self) -> ComposeResult:
        score, total = self.quiz.score, self.quiz.total
        percent = 0 if total == 0 else round(100 * score / total)

        with Horizontal(id="summary"):
            yield Digits(str(score), id="final-score", classes="tile")
            yield Digits(str(percent), id="final-percent", classes="tile")
            yield ProgressTile(id="final-progress", classes="tile")

        with Horizontal(id="results-board"):
            missed = self.quiz.missed()
            if missed:
                with VerticalScroll(id="missed"):
                    yield ItemGrid(
                        *(
                            Label(f"{c.flag} {c.name}", classes="missed-item")
                            for c in missed
                        ),
                        id="missed-grid",
                        min_column_width=COLUMN_WIDTH,
                    )
            else:
                yield Static("perfect — every country named", id="perfect")
            yield RegionPanel(id="breakdown")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#final-score").border_title = "found"
        self.query_one("#final-percent").border_title = "percent"
        self.query_one("#final-progress").border_title = f"{self.quiz_title} · result"
        self.query_one("#breakdown").border_title = "by region"
        if missed := self.quiz.missed():
            self.query_one("#missed").border_title = f"missed ({len(missed)})"
        else:
            self.query_one("#perfect").border_title = "missed (0)"

        progress = self.query_one(ProgressTile)
        progress.done = self.quiz.score
        progress.total = self.quiz.total
        self.query_one(RegionPanel).show(self.quiz.region_progress())

    def on_resize(self) -> None:
        self.set_class(self.size.width < NARROW_WIDTH, "-narrow")
        self.query_one(RegionPanel).show(self.quiz.region_progress())

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def action_replay(self) -> None:
        self.app.switch_screen(
            QuizScreen(self.quiz.countries, self.quiz.duration, title=self.quiz_title)
        )


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
