"""Tests for logsnap.differ and logsnap.cli_diff."""

from __future__ import annotations

import tarfile
import io
from pathlib import Path

import pytest

from logsnap.differ import diff_archives, DiffResult, _read_service_line_counts
from logsnap.cli_diff import build_diff_parser, run_diff_command


def _make_archive(tmp_path: Path, name: str, entries: dict[str, str]) -> Path:
    """Create a minimal tar.gz archive with given {service_name: log_content} entries."""
    archive_path = tmp_path / name
    with tarfile.open(archive_path, "w:gz") as tar:
        for svc, content in entries.items():
            data = content.encode()
            info = tarfile.TarInfo(name=f"{svc}.log")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return archive_path


@pytest.fixture()
def archive_dir(tmp_path):
    return tmp_path


def test_read_service_line_counts(archive_dir):
    arch = _make_archive(archive_dir, "snap.tar.gz", {"web": "line1\nline2\nline3\n", "db": "only one\n"})
    counts = _read_service_line_counts(arch)
    assert counts["web"] == 3
    assert counts["db"] == 1


def test_diff_no_changes(archive_dir):
    content = {"web": "a\nb\nc\n"}
    a = _make_archive(archive_dir, "a.tar.gz", content)
    b = _make_archive(archive_dir, "b.tar.gz", content)
    result = diff_archives(a, b)
    assert not result.has_changes
    assert result.added_services == []
    assert result.removed_services == []
    assert result.changed_services == {}


def test_diff_detects_added_service(archive_dir):
    a = _make_archive(archive_dir, "a.tar.gz", {"web": "line\n"})
    b = _make_archive(archive_dir, "b.tar.gz", {"web": "line\n", "worker": "new\n"})
    result = diff_archives(a, b)
    assert "worker" in result.added_services
    assert result.removed_services == []


def test_diff_detects_removed_service(archive_dir):
    a = _make_archive(archive_dir, "a.tar.gz", {"web": "x\n", "cache": "y\n"})
    b = _make_archive(archive_dir, "b.tar.gz", {"web": "x\n"})
    result = diff_archives(a, b)
    assert "cache" in result.removed_services


def test_diff_detects_line_count_change(archive_dir):
    a = _make_archive(archive_dir, "a.tar.gz", {"api": "line1\nline2\n"})
    b = _make_archive(archive_dir, "b.tar.gz", {"api": "line1\nline2\nline3\nline4\n"})
    result = diff_archives(a, b)
    assert "api" in result.changed_services
    assert result.changed_services["api"] == (2, 4)


def test_summary_contains_archive_names(archive_dir):
    a = _make_archive(archive_dir, "snap_old.tar.gz", {"svc": "a\n"})
    b = _make_archive(archive_dir, "snap_new.tar.gz", {"svc": "a\nb\n"})
    result = diff_archives(a, b)
    summary = result.summary()
    assert "snap_old.tar.gz" in summary
    assert "snap_new.tar.gz" in summary


def test_cli_diff_missing_archive(archive_dir, capsys):
    parser = build_diff_parser()
    args = parser.parse_args([str(archive_dir / "nope_a.tar.gz"), str(archive_dir / "nope_b.tar.gz")])
    code = run_diff_command(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_cli_diff_prints_summary(archive_dir, capsys):
    a = _make_archive(archive_dir, "a.tar.gz", {"web": "x\n"})
    b = _make_archive(archive_dir, "b.tar.gz", {"web": "x\ny\n"})
    parser = build_diff_parser()
    args = parser.parse_args([str(a), str(b)])
    run_diff_command(args)
    captured = capsys.readouterr()
    assert "web" in captured.out
