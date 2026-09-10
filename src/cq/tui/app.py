"""The cq terminal country-guessing game."""

from textual.app import App

from cq.tui.menu import MenuScreen
from cq.tui.theme import CQ_THEME


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
