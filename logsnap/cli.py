"""Main CLI entry point for logsnap.

Wires together all subcommands: snapshot, filter, output, and retention.
"""

import argparse
import sys

from logsnap.cli_filter import add_filter_args, filter_config_from_args
from logsnap.cli_output import add_output_args, format_options_from_args, print_result
from logsnap.cli_retention import add_retention_args, retention_policy_from_args, run_retention_command
from logsnap.config_init import load_or_init_config
from logsnap.snapshot import run_snapshot


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the 'snapshot' subcommand."""
    p = subparsers.add_parser(
        "snapshot",
        help="Capture logs from all configured services into a timestamped archive.",
    )
    p.add_argument(
        "--config",
        default="logsnap.yaml",
        metavar="FILE",
        help="Path to the logsnap config file (default: logsnap.yaml).",
    )
    add_filter_args(p)
    add_output_args(p)
    return p


def build_retention_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the 'retention' subcommand."""
    p = subparsers.add_parser(
        "retention",
        help="Apply retention policy to existing log archives.",
    )
    p.add_argument(
        "--config",
        default="logsnap.yaml",
        metavar="FILE",
        help="Path to the logsnap config file (default: logsnap.yaml).",
    )
    add_retention_args(p)
    return p


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="logsnap",
        description="Capture, filter, and snapshot structured logs from multiple services.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    build_snapshot_parser(subparsers)
    build_retention_subparser(subparsers)

    return parser


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Handle the 'snapshot' subcommand."""
    try:
        config = load_or_init_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"logsnap: failed to load config '{args.config}': {exc}", file=sys.stderr)
        return 1

    filter_cfg = filter_config_from_args(args)
    fmt_opts = format_options_from_args(args)

    result = run_snapshot(config, filter_cfg=filter_cfg)
    print_result(result, fmt_opts)

    return 0 if result.success else 1


def cmd_retention(args: argparse.Namespace) -> int:
    """Handle the 'retention' subcommand."""
    try:
        config = load_or_init_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"logsnap: failed to load config '{args.config}': {exc}", file=sys.stderr)
        return 1

    policy = retention_policy_from_args(args)
    archive_dir = config.archive_dir
    dry_run = getattr(args, "dry_run", False)

    run_retention_command(archive_dir, policy, dry_run=dry_run)
    return 0


_COMMAND_HANDLERS = {
    "snapshot": cmd_snapshot,
    "retention": cmd_retention,
}


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the appropriate subcommand handler."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = _COMMAND_HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
