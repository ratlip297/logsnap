"""CLI output helpers — wires formatter into argparse-based CLI."""

import argparse
import sys
from typing import Optional

from logsnap.formatter import FormatOptions, format_result, format_summary_line
from logsnap.snapshot import SnapshotResult


def add_output_args(parser: argparse.ArgumentParser) -> None:
    """Attach output-related flags to an existing argument parser."""
    group = parser.add_argument_group("output")
    group.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Show per-service line counts in output",
    )
    group.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color codes in output",
    )
    group.add_argument(
        "--log-summary",
        action="store_true",
        default=False,
        help="Print a machine-readable one-line summary to stderr",
    )


def format_options_from_args(args: argparse.Namespace) -> FormatOptions:
    """Build a FormatOptions instance from parsed CLI args."""
    return FormatOptions(
        verbose=getattr(args, "verbose", False),
        color=not getattr(args, "no_color", False),
        show_archive_path=True,
    )


def print_result(
    result: SnapshotResult,
    args: argparse.Namespace,
    out=None,
    err=None,
) -> None:
    """Print formatted snapshot result to stdout (and optionally summary to stderr)."""
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    options = format_options_from_args(args)
    print(format_result(result, options), file=out)

    if getattr(args, "log_summary", False):
        print(format_summary_line(result), file=err)


def build_output_parser() -> argparse.ArgumentParser:
    """Standalone parser for testing output flags."""
    parser = argparse.ArgumentParser(prog="logsnap-output-test")
    add_output_args(parser)
    return parser
