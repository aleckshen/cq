"""Small helpers and the widgets shared by the quiz and results screens."""

import math
from collections.abc import Iterable

from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Static

from cq.countries import Country
from cq.tui.theme import COLUMN_WIDTH


def track(done: int, total: int, width: int) -> Content:
    """A progress track `width` cells wide: earned cells are solid white, the
    rest a light shade."""
    width = max(width, 1)
    filled = 0 if total <= 0 else round(width * done / total)
    filled = max(0, min(width, filled))
    return Content.styled("█" * filled, "white") + Content.styled(
        "░" * (width - filled), "$text-disabled"
    )


def clock(seconds: float) -> str:
    """Round *up* so a fresh 15:00 quiz reads 15:00, not 14:59."""
    total = max(0, math.ceil(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


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
                Content.styled(f"{percent}%".center(width), "bold white"),
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


class CountryColumns(Static):
    """A flag+name list, sorted alphabetically and laid out in newspaper
    columns: each column is filled top-to-bottom to the height of the visible
    area before the next one starts. Only when the columns would overflow the
    width does it fall back to balanced columns and scroll vertically."""

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._countries: list[Country] = []

    def set_countries(self, countries: Iterable[Country]) -> None:
        self._countries = sorted(countries, key=lambda c: c.name)
        self.refresh(layout=True)

    def on_resize(self) -> None:
        self.refresh(layout=True)

    def render(self) -> Content:
        count = len(self._countries)
        # the visible area is the scroll viewport (our parent), not our own
        # auto height, which only ever reports the content we last produced.
        viewport = self.parent.content_size if self.parent else self.container_size
        width, height = viewport.width, viewport.height
        if not count or width < 1:
            return Content("")

        max_columns = max(1, (width + 1) // (COLUMN_WIDTH + 1))
        rows = max(1, height)
        if -(-count // rows) > max_columns:  # wider than the area — let it scroll
            rows = -(-count // max_columns)
        columns = -(-count // rows)

        lines = [
            Content(" ").join(
                Content(
                    f"{self._countries[i].flag} {self._countries[i].name}"
                ).truncate(COLUMN_WIDTH, ellipsis=True, pad=True)
                for column in range(columns)
                if (i := column * rows + row) < count
            )
            for row in range(rows)
        ]
        return Content("\n").join(lines)
