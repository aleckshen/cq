"""Final score, region breakdown, and the countries that got away."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Digits, Footer, Static

from cq.game import Quiz
from cq.tui.theme import COUNT_WIDTH, NARROW_WIDTH, SIDEBAR_WIDTH
from cq.tui.widgets import CountryColumns, ProgressTile, RegionPanel


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
        color: white;
    }}
    ResultsScreen #final-percent {{
        width: {COUNT_WIDTH};
        text-align: center;
        color: white;
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
    }}
    ResultsScreen #perfect {{
        width: 1fr;
        height: 100%;
        border: round $success;
        border-title-align: left;
        border-title-color: white;
        content-align: center middle;
        color: white;
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
            if self.quiz.missed():
                with VerticalScroll(id="missed"):
                    yield CountryColumns(id="missed-grid")
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
            self.query_one(CountryColumns).set_countries(missed)
        else:
            self.query_one("#perfect").border_title = "missed (0)"

        progress = self.query_one(ProgressTile)
        progress.done = self.quiz.score
        progress.total = self.quiz.total
        self.query_one(RegionPanel).show(self.quiz.region_progress())

    def on_resize(self) -> None:
        self.set_class(self.size.width < NARROW_WIDTH, "-narrow")
        self.query_one(RegionPanel).show(self.quiz.region_progress())
        for grid in self.query(CountryColumns):
            grid.refresh(layout=True)

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def action_replay(self) -> None:
        from cq.tui.quiz import QuizScreen

        self.app.switch_screen(
            QuizScreen(self.quiz.countries, self.quiz.duration, title=self.quiz_title)
        )
