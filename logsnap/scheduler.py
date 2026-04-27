"""Simple cron-style schedule support for automated snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SCHEDULE_FILE_NAME = ".logsnap_schedule.json"


@dataclass
class ScheduleEntry:
    service: str
    cron: str
    enabled: bool = True
    last_run: Optional[str] = None


@dataclass
class ScheduleConfig:
    entries: list[ScheduleEntry] = field(default_factory=list)
    schedule_file: str = SCHEDULE_FILE_NAME


def _entry_from_dict(d: dict) -> ScheduleEntry:
    return ScheduleEntry(
        service=d["service"],
        cron=d["cron"],
        enabled=d.get("enabled", True),
        last_run=d.get("last_run"),
    )


def _entry_to_dict(e: ScheduleEntry) -> dict:
    return {
        "service": e.service,
        "cron": e.cron,
        "enabled": e.enabled,
        "last_run": e.last_run,
    }


def load_schedule(path: str | Path) -> ScheduleConfig:
    """Load schedule entries from a JSON file."""
    p = Path(path)
    if not p.exists():
        return ScheduleConfig(schedule_file=str(path))
    with p.open() as fh:
        raw = json.load(fh)
    entries = [_entry_from_dict(d) for d in raw.get("entries", [])]
    return ScheduleConfig(entries=entries, schedule_file=str(path))


def save_schedule(config: ScheduleConfig) -> None:
    """Persist schedule config back to its file."""
    p = Path(config.schedule_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"entries": [_entry_to_dict(e) for e in config.entries]}
    with p.open("w") as fh:
        json.dump(data, fh, indent=2)


def add_or_update_entry(config: ScheduleConfig, entry: ScheduleEntry) -> None:
    """Add a new entry or replace an existing one with the same service name."""
    for i, existing in enumerate(config.entries):
        if existing.service == entry.service:
            config.entries[i] = entry
            return
    config.entries.append(entry)


def remove_entry(config: ScheduleConfig, service: str) -> bool:
    """Remove an entry by service name. Returns True if found and removed."""
    before = len(config.entries)
    config.entries = [e for e in config.entries if e.service != service]
    return len(config.entries) < before


def list_enabled(config: ScheduleConfig) -> list[ScheduleEntry]:
    """Return only enabled entries."""
    return [e for e in config.entries if e.enabled]
