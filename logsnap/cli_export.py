"""CLI helpers for the export sub-command."""
from __future__ import annotations

import argparse
from pathlib import Path

from logsnap.exporter import ExportOptions, export_archive, write_export


def add_export_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("archive", type=Path, help="Path to the .tar.gz archive to export")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        dest="export_format",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write output to this file instead of stdout",
    )
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        default=False,
        help="Disable pretty-printing for JSON output",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        default=False,
        help="Omit metadata envelope from output",
    )


def export_options_from_args(args: argparse.Namespace) -> ExportOptions:
    return ExportOptions(
        format=args.export_format,
        pretty=not args.no_pretty,
        include_metadata=not args.no_metadata,
    )


def run_export_command(args: argparse.Namespace) -> int:
    """Execute the export sub-command; returns an exit code."""
    archive: Path = args.archive
    if not archive.exists():
        print(f"error: archive not found: {archive}")
        return 1

    options = export_options_from_args(args)

    if args.output:
        dest: Path = args.output
        write_export(archive, dest, options)
        print(f"Exported to {dest}")
    else:
        print(export_archive(archive, options))

    return 0


def build_export_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a logsnap archive to JSON or CSV")
    add_export_args(parser)
    return parser
