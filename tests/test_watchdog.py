"""Tests for logsnap.watchdog."""

import tarfile
from pathlib import Path

import pytest

from logsnap.watchdog import WatchdogConfig, WatchdogReport, run_watchdog


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_archive(directory: Path, name: str, content: str = "hello\n") -> Path:
    """Create a minimal .tar.gz archive file in *directory*."""
    archive_path = directory / name
    inner = directory / "_tmp.txt"
    inner.write_text(content)
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(inner, arcname="log.txt")
    inner.unlink()
    return archive_path


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def archive_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_empty_dir_is_ok(archive_dir: Path):
    cfg = WatchdogConfig(archive_dir=str(archive_dir))
    report = run_watchdog(cfg)
    assert report.ok
    assert report.archive_count == 0
    assert report.total_size_bytes == 0


def test_count_within_limit_no_alert(archive_dir: Path):
    _make_archive(archive_dir, "logsnap_20240101_120000.tar.gz")
    _make_archive(archive_dir, "logsnap_20240102_120000.tar.gz")
    cfg = WatchdogConfig(archive_dir=str(archive_dir), max_archive_count=5)
    report = run_watchdog(cfg)
    assert report.ok
    assert report.archive_count == 2


def test_count_exceeds_limit_raises_alert(archive_dir: Path):
    for i in range(4):
        _make_archive(archive_dir, f"logsnap_2024010{i+1}_120000.tar.gz")
    cfg = WatchdogConfig(archive_dir=str(archive_dir), max_archive_count=3)
    report = run_watchdog(cfg)
    assert not report.ok
    assert any(a.kind == "count" for a in report.alerts)


def test_size_within_limit_no_alert(archive_dir: Path):
    _make_archive(archive_dir, "logsnap_20240101_120000.tar.gz")
    cfg = WatchdogConfig(archive_dir=str(archive_dir), max_total_size_mb=100.0)
    report = run_watchdog(cfg)
    assert report.ok


def test_size_exceeds_limit_raises_alert(archive_dir: Path):
    _make_archive(archive_dir, "logsnap_20240101_120000.tar.gz", content="x" * 1024)
    cfg = WatchdogConfig(archive_dir=str(archive_dir), max_total_size_mb=0.000001)
    report = run_watchdog(cfg)
    assert not report.ok
    assert any(a.kind == "size" for a in report.alerts)


def test_multiple_alerts_possible(archive_dir: Path):
    for i in range(3):
        _make_archive(archive_dir, f"logsnap_2024010{i+1}_120000.tar.gz", content="x" * 512)
    cfg = WatchdogConfig(
        archive_dir=str(archive_dir),
        max_archive_count=2,
        max_total_size_mb=0.000001,
    )
    report = run_watchdog(cfg)
    assert len(report.alerts) == 2


def test_summary_ok_contains_ok(archive_dir: Path):
    cfg = WatchdogConfig(archive_dir=str(archive_dir))
    report = run_watchdog(cfg)
    assert "OK" in report.summary()


def test_summary_alert_contains_alert_info(archive_dir: Path):
    for i in range(3):
        _make_archive(archive_dir, f"logsnap_2024010{i+1}_120000.tar.gz")
    cfg = WatchdogConfig(archive_dir=str(archive_dir), max_archive_count=1)
    report = run_watchdog(cfg)
    summary = report.summary()
    assert "COUNT" in summary
    assert "alert" in summary.lower()
