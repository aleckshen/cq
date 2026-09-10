# cq

A terminal country-guessing game. Name as many of the world's 197 countries as
you can before the clock runs out. Built with [Textual](https://textual.textualize.io/).

## Install

Requires Python 3.13+. With [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

## Run

```sh
uv run cq
# or, once the environment is active
cq
python -m cq
```

## How to play

Pick a quiz from the menu. The whole world, or a single region (Africa, Asia,
Europe, North America, Oceania, South America). You get 15 minutes.

- **Type a country name.** No need to press Enter; a match is claimed the moment
  you finish typing it. Accents, casing, and punctuation don't matter, and common
  alternate names work (`Türkiye`/`Turkey`, `Cabo Verde`/`Cape Verde`, `Kosova`).
- The HUD tracks time left, your score, and overall progress; the sidebar breaks
  progress down by region, and found countries fill in alphabetically.
- **Esc** pauses and holds the clock. Resume, or give up to see your results.
- **Ctrl+R** restarts the current quiz.

The results screen shows your final score, the countries you missed, and a
per-region breakdown. Press **R** to replay the same quiz.

## Development

`uv sync` installs the package as an editable install alongside the dev
dependencies, so source changes are picked up on the next run (the TUI has no
hot reload, so restart it to see changes).

```sh
uv run pytest        # the full suite
uvx ruff check src   # lint
```

The game logic is covered by fast unit tests (`test_countries.py`,
`test_game.py`, `test_matching.py`); the interface is driven end-to-end with
Textual's `run_test` pilot in `test_tui.py`: opening a quiz, typing guesses,
pausing, finishing, and replaying.

## Layout

The pure game rules (`game.py`, `matching.py`, `countries.py`) do no I/O and
know nothing about Textual; the `tui/` package is the interface layer on top,
one module per screen.

```
src/cq/
├── cli.py          argument parsing and launch
├── countries.py    the Country model and the cached dataset loader
├── matching.py     fold a guess to a comparable form; match it to a name/alias
├── game.py         pure game state: score, countdown, the answered set
├── data/
│   └── countries.json
└── tui/
    ├── app.py      the Textual App, theme registration, first screen
    ├── theme.py    the cq theme, ASCII banner, shared layout dimensions
    ├── menu.py     landing screen, pick the whole world or one region
    ├── quiz.py     the timed quiz HUD, the guess input, and the pause modal
    ├── results.py  final score, missed countries, per-region breakdown
    └── widgets.py  the progress bars, region sidebar, and country-column list
```

## Data

`src/cq/data/countries.json` holds all 197 sovereign states (the 193 UN members
plus Vatican City, Palestine, Taiwan, and Kosovo), each with its name, official
name, alternate names, capital(s), region, and flag.
