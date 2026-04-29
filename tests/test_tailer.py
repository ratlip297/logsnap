"""Tests for logsnap.tailer and logsnap.cli_tail."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest

from logsnap.config import ServiceConfig
from logsnap.filter import FilterConfig
from logsnap.tailer import TailOptions, _tail_file, tail_service
from logsnap.cli_tail import build_tail_parser, run_tail_command
from logsnap.config import SnapConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("\n".join(f"line {i}" for i in range(1, 31)) + "\n")
    return p


@pytest.fixture()
def file_service(log_file: Path) -> ServiceConfig:
    return ServiceConfig(name="app", log_path=str(log_file))


@pytest.fixture()
def cmd_service() -> ServiceConfig:
    return ServiceConfig(name="cmd_svc", command="echo 'hello world'")


# ---------------------------------------------------------------------------
# _tail_file
# ---------------------------------------------------------------------------

def test_tail_file_returns_last_n_lines(log_file: Path):
    lines = _tail_file(log_file, 5)
    assert len(lines) == 5
    assert "line 30" in lines[-1]


def test_tail_file_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _tail_file(tmp_path / "nope.log", 10)


# ---------------------------------------------------------------------------
# tail_service
# ---------------------------------------------------------------------------

def test_tail_service_file(file_service: ServiceConfig):
    opts = TailOptions(lines=10)
    lines = tail_service(file_service, opts)
    assert len(lines) == 10


def test_tail_service_applies_filter(file_service: ServiceConfig):
    opts = TailOptions(lines=30, filter_config=FilterConfig(include_patterns=["line 2"]))
    lines = tail_service(file_service, opts)
    # only lines containing "line 2" (line 2, 20, 21...29)
    assert all("line 2" in l for l in lines)


def test_tail_service_command():
    svc = ServiceConfig(name="echo", command="printf 'a\\nb\\nc\\n'")
    opts = TailOptions(lines=2)
    lines = tail_service(svc, opts)
    assert len(lines) == 2


def test_tail_service_no_source_raises():
    svc = ServiceConfig(name="empty")
    with pytest.raises(ValueError, match="no command or log_path"):
        tail_service(svc, TailOptions())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def snap_config(file_service: ServiceConfig) -> SnapConfig:
    return SnapConfig(services=[file_service], output_dir="/tmp")


def test_run_tail_command_all_services(snap_config: SnapConfig):
    parser = build_tail_parser()
    args = parser.parse_args(["-n", "5"])
    out = io.StringIO()
    code = run_tail_command(args, snap_config, out=out)
    assert code == 0
    assert "==> app <==" in out.getvalue()


def test_run_tail_command_unknown_service(snap_config: SnapConfig):
    parser = build_tail_parser()
    args = parser.parse_args(["unknown"])
    err = io.StringIO()
    code = run_tail_command(args, snap_config, err=err)
    assert code == 1
    assert "not found" in err.getvalue()
