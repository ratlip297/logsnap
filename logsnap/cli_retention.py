"""CLI interface for retention policy commands."""

import argparse
from logsnap.retention import RetentionPolicy, list_archives, apply_retention


def add_retention_args(parser: argparse.ArgumentParser) -> None:
    """Add retention-related arguments to a parser."""
    parser.add_argument(
        "--max-archives",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N most recent archives.",
    )
    parser.add_argument(
        "--max-age-days",
        type=float,
        default=None,
        metavar="DAYS",
        help="Delete archives older than DAYS days.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be deleted without actually deleting.",
    )
    parser.add_argument(
        "archive_dir",
        help="Directory containing logsnap archives.",
    )


def retention_policy_from_args(args: argparse.Namespace) -> RetentionPolicy:
    """Build a RetentionPolicy from parsed CLI args."""
    return RetentionPolicy(
        max_archives=args.max_archives,
        max_age_days=args.max_age_days,
    )


def run_retention_command(args: argparse.Namespace) -> int:
    """Execute the retention command. Returns exit code."""
    policy = retention_policy_from_args(args)
    archives = list_archives(args.archive_dir)

    if not archives:
        print("No archives found.")
        return 0

    deleted = apply_retention(args.archive_dir, policy, dry_run=args.dry_run)

    prefix = "[dry-run] Would delete" if args.dry_run else "Deleted"
    for path in deleted:
        print(f"{prefix}: {path}")

    if deleted:
        print(f"{prefix} {len(deleted)} archive(s).")
    else:
        print("No archives removed.")

    return 0


def build_retention_parser() -> argparse.ArgumentParser:
    """Build a standalone argument parser for the retention subcommand."""
    parser = argparse.ArgumentParser(
        prog="logsnap retention",
        description="Apply retention policy to logsnap archives.",
    )
    add_retention_args(parser)
    return parser
