"""Landing screen: a centered dashboard to pick which quiz to start."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from cq.countries import Country, load_countries
from cq.tui.theme import BANNER, MENU_ROW_WIDTH, MENU_WIDTH


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
            pointer = Content.styled("❯ ", "white")
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
        color: white;
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
            border: round white;
            border-title-color: white;
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
        from cq.tui.quiz import QuizScreen

        if event.entry.key == "quit":
            self.app.exit()
            return
        self.app.push_screen(QuizScreen(event.entry.countries, title=event.entry.label))

    def action_quit_app(self) -> None:
        self.app.exit()
