"""CLI helpers for the `logsnap tail` sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logsnap.cli_filter import add_filter_args, filter_config_from_args
from logsnap.config import SnapConfig
from logsnap.tailer import TailOptions, tail_service


def add_tail_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "service",
        nargs="?",
        default=None,
        help="Service name to tail (default: all services)",
    )
    parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=20,
        metavar="N",
        help="Number of lines to show per service (default: 20)",
    )
    add_filter_args(parser)


def tail_options_from_args(args: argparse.Namespace) -> TailOptions:
    return TailOptions(
        lines=args.lines,
        filter_config=filter_config_from_args(args),
    )


def run_tail_command(
    args: argparse.Namespace,
    config: SnapConfig,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    options = tail_options_from_args(args)

    services = (
        [s for s in config.services if s.name == args.service]
        if args.service
        else config.services
    )

    if not services:
        name = args.service or "(none configured)"
        print(f"error: service '{name}' not found in config.", file=err)
        return 1

    exit_code = 0
    for svc in services:
        print(f"==> {svc.name} <==", file=out)
        try:
            lines = tail_service(svc, options)
            for line in lines:
                print(line, file=out)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            print(f"error: {exc}", file=err)
            exit_code = 1
        print("", file=out)

    return exit_code


def build_tail_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logsnap tail",
        description="Show the last N lines from one or all service logs.",
    )
    add_tail_args(parser)
    return parser
