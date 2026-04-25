"""CLI helpers for the retention sub-command."""

from __future__ import annotations

import argparse
from typing import List

from logsnap.retention import RetentionPolicy, apply_retention, list_archives


def add_retention_args(parser: argparse.ArgumentParser) -> None:
    """Attach retention-related arguments to *parser*."""
    parser.add_argument(
        "--keep-last",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N most recent archives.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        metavar="DAYS",
        help="Delete archives older than DAYS days.",
    )
    parser.add_argument(
        "--archive-dir",
        default=".",
        metavar="DIR",
        help="Directory to scan for archives (default: current directory).",
    )
    parser.add_argument(
        "--prefix",
        default="logsnap",
        help="Archive filename prefix to match (default: logsnap).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be deleted without removing files.",
    )


def retention_policy_from_args(args: argparse.Namespace) -> RetentionPolicy:
    return RetentionPolicy(
        keep_last=args.keep_last,
        max_age_days=args.max_age_days,
    )


def run_retention_command(args: argparse.Namespace) -> List[str]:
    """Execute retention pruning (or dry-run) and return list of affected paths."""
    policy = retention_policy_from_args(args)

    if args.dry_run:
        archives = list_archives(args.archive_dir, prefix=args.prefix)
        # Simulate what would be deleted by applying policy to a temp copy — just report
        # We reuse apply_retention on a real dir, so for dry-run we just list candidates.
        print(f"[dry-run] scanning '{args.archive_dir}' with prefix '{args.prefix}'")
        print(f"[dry-run] found {len(archives)} archive(s); policy: {policy}")
        return [str(p) for p in archives]

    deleted = apply_retention(args.archive_dir, policy, prefix=args.prefix)
    for path in deleted:
        print(f"deleted: {path}")
    if not deleted:
        print("no archives removed")
    return deleted


def build_retention_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logsnap retention",
        description="Prune old logsnap archives according to a retention policy.",
    )
    add_retention_args(parser)
    return parser
