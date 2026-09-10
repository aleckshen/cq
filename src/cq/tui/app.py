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
    Footer FooterKey .footer-key--key {
        color: $primary;
        background: $surface;
    }
    Footer FooterKey .footer-key--description {
        color: $text-muted;
        background: $surface;
    }
    Footer FooterKey.-command-palette {
        border-left: none;
    }
    """

    def on_mount(self) -> None:
        self.register_theme(CQ_THEME)
        self.theme = "cq"
        self.push_screen(MenuScreen())
