"""CLI support for the 'diff' subcommand."""

from __future__ import annotations

import argparse
from pathlib import Path

from logsnap.differ import diff_archives, DiffResult


def add_diff_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "archive_a",
        metavar="ARCHIVE_A",
        help="Path to the first (older) archive.",
    )
    parser.add_argument(
        "archive_b",
        metavar="ARCHIVE_B",
        help="Path to the second (newer) archive.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output.",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        default=False,
        help="Only report services that changed; skip unchanged.",
    )


def run_diff_command(args: argparse.Namespace) -> int:
    """Execute the diff command. Returns exit code."""
    path_a = Path(args.archive_a)
    path_b = Path(args.archive_b)

    for p in (path_a, path_b):
        if not p.exists():
            print(f"error: archive not found: {p}")
            return 1

    result: DiffResult = diff_archives(path_a, path_b)

    if args.changed_only and not result.has_changes:
        return 0

    print(result.summary())
    return 0 if result.has_changes is not None else 0


def build_diff_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logsnap diff",
        description="Compare two logsnap archives and show differences.",
    )
    add_diff_args(parser)
    return parser
