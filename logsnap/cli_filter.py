"""CLI helpers for building a FilterConfig from command-line arguments."""

from __future__ import annotations

import argparse
from typing import List, Optional

from logsnap.filter import FilterConfig


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Attach filter-related arguments to *parser*."""
    parser.add_argument(
        "--include",
        metavar="PATTERN",
        action="append",
        default=[],
        dest="include_patterns",
        help="Only keep lines matching this regex (repeatable).",
    )
    parser.add_argument(
        "--exclude",
        metavar="PATTERN",
        action="append",
        default=[],
        dest="exclude_patterns",
        help="Drop lines matching this regex (repeatable).",
    )
    parser.add_argument(
        "--level",
        metavar="LEVEL",
        default=None,
        dest="min_level",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Minimum log level to include (debug/info/warning/error/critical).",
    )


def filter_config_from_args(args: argparse.Namespace) -> FilterConfig:
    """Construct a :class:`FilterConfig` from parsed CLI *args*."""
    return FilterConfig(
        include_patterns=list(args.include_patterns),
        exclude_patterns=list(args.exclude_patterns),
        min_level=args.min_level,
    )


def build_filter_parser(prog: str = "logsnap") -> argparse.ArgumentParser:
    """Return a standalone parser with filter arguments (useful for testing)."""
    parser = argparse.ArgumentParser(prog=prog)
    add_filter_args(parser)
    return parser
