"""Small helpers and the widgets shared by the quiz and results screens."""

import math

from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Static


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
