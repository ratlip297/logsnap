"""CLI subcommand for managing logsnap schedules."""

from __future__ import annotations

import argparse

from logsnap.scheduler import (
    ScheduleEntry,
    load_schedule,
    save_schedule,
    add_or_update_entry,
    remove_entry,
    list_enabled,
    SCHEDULE_FILE_NAME,
)


def build_schedule_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Manage automated snapshot schedules"
    if subparsers is not None:
        p = subparsers.add_parser("schedule", help=desc)
    else:
        p = argparse.ArgumentParser(prog="logsnap schedule", description=desc)

    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    # list
    sub.add_parser("list", help="List all schedule entries")

    # add
    add_p = sub.add_parser("add", help="Add or update a schedule entry")
    add_p.add_argument("service", help="Service name")
    add_p.add_argument("cron", help="Cron expression, e.g. '0 * * * *'")
    add_p.add_argument("--disabled", action="store_true", help="Add entry as disabled")

    # remove
    rm_p = sub.add_parser("remove", help="Remove a schedule entry")
    rm_p.add_argument("service", help="Service name to remove")

    p.add_argument(
        "--schedule-file",
        default=SCHEDULE_FILE_NAME,
        help="Path to schedule JSON file",
    )
    return p


def run_schedule_command(args: argparse.Namespace) -> int:
    config = load_schedule(args.schedule_file)

    if args.schedule_cmd == "list":
        if not config.entries:
            print("No schedule entries defined.")
            return 0
        for e in config.entries:
            status = "enabled" if e.enabled else "disabled"
            last = e.last_run or "never"
            print(f"  {e.service:<20} {e.cron:<20} [{status}]  last_run={last}")
        return 0

    if args.schedule_cmd == "add":
        entry = ScheduleEntry(
            service=args.service,
            cron=args.cron,
            enabled=not args.disabled,
        )
        add_or_update_entry(config, entry)
        save_schedule(config)
        print(f"Saved schedule for '{args.service}' ({args.cron}).")
        return 0

    if args.schedule_cmd == "remove":
        found = remove_entry(config, args.service)
        if not found:
            print(f"No entry found for service '{args.service}'.")
            return 1
        save_schedule(config)
        print(f"Removed schedule for '{args.service}'.")
        return 0

    return 1
