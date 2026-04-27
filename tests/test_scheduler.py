"""Tests for logsnap.scheduler and logsnap.cli_scheduler."""

from __future__ import annotations

import json
import argparse
import pytest
from pathlib import Path

from logsnap.scheduler import (
    ScheduleEntry,
    ScheduleConfig,
    load_schedule,
    save_schedule,
    add_or_update_entry,
    remove_entry,
    list_enabled,
)
from logsnap.cli_scheduler import build_schedule_parser, run_schedule_command


@pytest.fixture
def schedule_file(tmp_path):
    return tmp_path / "schedule.json"


def _write_schedule(path, entries):
    path.write_text(json.dumps({"entries": entries}))


def test_load_schedule_missing_returns_empty(schedule_file):
    cfg = load_schedule(schedule_file)
    assert cfg.entries == []


def test_load_schedule_parses_entries(schedule_file):
    _write_schedule(schedule_file, [
        {"service": "web", "cron": "0 * * * *", "enabled": True, "last_run": None}
    ])
    cfg = load_schedule(schedule_file)
    assert len(cfg.entries) == 1
    assert cfg.entries[0].service == "web"
    assert cfg.entries[0].cron == "0 * * * *"


def test_save_and_reload_roundtrip(schedule_file):
    cfg = ScheduleConfig(schedule_file=str(schedule_file))
    add_or_update_entry(cfg, ScheduleEntry(service="db", cron="30 2 * * *"))
    save_schedule(cfg)
    reloaded = load_schedule(schedule_file)
    assert len(reloaded.entries) == 1
    assert reloaded.entries[0].service == "db"


def test_add_or_update_replaces_existing():
    cfg = ScheduleConfig()
    add_or_update_entry(cfg, ScheduleEntry(service="svc", cron="0 1 * * *"))
    add_or_update_entry(cfg, ScheduleEntry(service="svc", cron="0 2 * * *"))
    assert len(cfg.entries) == 1
    assert cfg.entries[0].cron == "0 2 * * *"


def test_remove_entry_returns_true_when_found():
    cfg = ScheduleConfig(entries=[ScheduleEntry(service="x", cron="* * * * *")])
    assert remove_entry(cfg, "x") is True
    assert cfg.entries == []


def test_remove_entry_returns_false_when_missing():
    cfg = ScheduleConfig()
    assert remove_entry(cfg, "ghost") is False


def test_list_enabled_excludes_disabled():
    cfg = ScheduleConfig(entries=[
        ScheduleEntry(service="a", cron="* * * * *", enabled=True),
        ScheduleEntry(service="b", cron="* * * * *", enabled=False),
    ])
    enabled = list_enabled(cfg)
    assert len(enabled) == 1
    assert enabled[0].service == "a"


def test_cli_add_and_list(schedule_file, capsys):
    parser = build_schedule_parser()
    args = parser.parse_args(["add", "myservice", "0 6 * * *", "--schedule-file", str(schedule_file)])
    assert run_schedule_command(args) == 0
    args2 = parser.parse_args(["list", "--schedule-file", str(schedule_file)])
    assert run_schedule_command(args2) == 0
    out = capsys.readouterr().out
    assert "myservice" in out


def test_cli_remove_missing_returns_nonzero(schedule_file):
    parser = build_schedule_parser()
    args = parser.parse_args(["remove", "nobody", "--schedule-file", str(schedule_file)])
    assert run_schedule_command(args) == 1


def test_cli_list_empty_prints_message(schedule_file, capsys):
    parser = build_schedule_parser()
    args = parser.parse_args(["list", "--schedule-file", str(schedule_file)])
    run_schedule_command(args)
    out = capsys.readouterr().out
    assert "No schedule" in out
