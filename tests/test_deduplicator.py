"""Tests for logsnap.deduplicator."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from logsnap.deduplicator import (
    DeduplicationResult,
    deduplicate_archive,
    deduplicate_service,
)


def _make_archive(tmp_path: Path, entries: dict[str, list[str]]) -> Path:
    """Create a .tar.gz archive where keys are member names and values are lines."""
    archive = tmp_path / "snap.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, lines in entries.items():
            data = "\n".join(lines).encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return archive


@pytest.fixture()
def archive_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_dedup_result_reduction_pct_zero_when_no_original():
    r = DeduplicationResult(
        service_name="svc",
        original_count=0,
        unique_count=0,
        duplicates_removed=0,
    )
    assert r.reduction_pct == 0.0


def test_dedup_result_reduction_pct_correct():
    r = DeduplicationResult(
        service_name="svc",
        original_count=10,
        unique_count=6,
        duplicates_removed=4,
    )
    assert r.reduction_pct == 40.0


def test_dedup_result_summary_contains_service_name():
    r = DeduplicationResult(
        service_name="myservice",
        original_count=5,
        unique_count=3,
        duplicates_removed=2,
    )
    assert "myservice" in r.summary()
    assert "5" in r.summary()
    assert "3" in r.summary()


def test_deduplicate_service_no_duplicates(archive_dir: Path):
    lines = ["line one", "line two", "line three"]
    archive = _make_archive(archive_dir, {"web.log": lines})
    result = deduplicate_service(archive, "web.log")
    assert result.service_name == "web"
    assert result.original_count == 3
    assert result.unique_count == 3
    assert result.duplicates_removed == 0
    assert result.top_duplicates == []


def test_deduplicate_service_with_duplicates(archive_dir: Path):
    lines = ["ERROR foo"] * 5 + ["INFO bar"] * 2 + ["DEBUG baz"]
    archive = _make_archive(archive_dir, {"api.log": lines})
    result = deduplicate_service(archive, "api.log")
    assert result.original_count == 8
    assert result.unique_count == 3
    assert result.duplicates_removed == 5
    top_lines = [line for line, _ in result.top_duplicates]
    assert "ERROR foo" in top_lines


def test_deduplicate_service_missing_member(archive_dir: Path):
    archive = _make_archive(archive_dir, {"web.log": ["hello"]})
    result = deduplicate_service(archive, "missing.log")
    assert result.original_count == 0
    assert result.duplicates_removed == 0


def test_deduplicate_archive_returns_all_log_members(archive_dir: Path):
    archive = _make_archive(
        archive_dir,
        {
            "web.log": ["a", "a", "b"],
            "db.log": ["x", "y"],
            "meta.json": ['{"ts": 1}'],
        },
    )
    results = deduplicate_archive(archive)
    assert set(results.keys()) == {"web", "db"}
    assert results["web"].duplicates_removed == 1
    assert results["db"].duplicates_removed == 0


def test_deduplicate_archive_empty(archive_dir: Path):
    archive = _make_archive(archive_dir, {})
    results = deduplicate_archive(archive)
    assert results == {}
