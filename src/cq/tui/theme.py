"""The cq theme, ASCII banner, and shared layout dimensions."""

from textual.theme import Theme

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
    foreground="#ffffff",
    # "ansi_default" + ansi=True is what actually gets Textual to leave these
    # cells unpainted rather than filling them with a literal color: without
    # ansi=True, Rich resolves "ansi_default" to an *approximate* solid RGB
    # (confirmed by capturing the raw escape codes) instead of emitting a
    # real terminal-default reset. The `variables` below are the ones
    # Textual's own ansi-mode CSS (cursor/selection colors, the inline-mode
    # border) expects to exist; copied from its built-in "ansi-dark" theme.
    background="ansi_default",
    surface="ansi_default",
    panel="ansi_default",
    dark=True,
    ansi=True,
    variables={
        "ansi-background": "ansi_black",
        "ansi-foreground": "ansi_white",
        "border-blurred": "ansi_black",
        "block-cursor-foreground": "ansi_black",
        "block-cursor-background": "ansi_white",
        "input-cursor-background": "ansi_black",
        "input-cursor-foreground": "ansi_bright_white",
        "input-cursor-text-style": "none",
        "input-selection-background": "ansi_bright_blue",
        "input-selection-foreground": "ansi_black",
        "screen-selection-background": "ansi_bright_blue",
        "screen-selection-foreground": "ansi_black",
        # every piece of body text renders pure white, including the shades
        # Textual would otherwise dim (captions, hints, border titles).
        "text": "#ffffff",
        "text-muted": "#ffffff",
        "text-disabled": "#ffffff",
    },
)
