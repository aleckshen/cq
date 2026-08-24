"""Command-line interface: argument parsing and game launch."""

import argparse

from cq.tui import CqApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cq", description="A terminal country guesser game"
    )
    parser.parse_args()
    CqApp().run()
