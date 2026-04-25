"""Tests for logsnap.retention."""

from __future__ import annotations

import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from logsnap.retention import (
    RetentionPolicy,
    _parse_timestamp,
    apply_retention,
    list_archives,
)


def _make_archive(directory: Path, timestamp: datetime, prefix: str = "logsnap") -> Path:
    name = f"{prefix}_{timestamp.strftime('%Y%m%dT%H%M%S')}.tar.gz"
    p = directory / name
    with tarfile.open(p, "w:gz"):
        pass
    return p


@pytest.fixture()
def archive_dir(tmp_path):
    return tmp_path


def test_parse_timestamp_valid():
    p = Path("logsnap_20240601T120000.tar.gz")
    ts = _parse_timestamp(p)
    assert ts == datetime(2024, 6, 1, 12, 0, 0)


def test_parse_timestamp_invalid():
    assert _parse_timestamp(Path("no_timestamp.tar.gz")) is None


def test_list_archives_sorted_oldest_first(archive_dir):
    now = datetime(2024, 6, 1, 12, 0, 0)
    p2 = _make_archive(archive_dir, now)
    p1 = _make_archive(archive_dir, now - timedelta(days=2))
    p3 = _make_archive(archive_dir, now + timedelta(days=1))
    result = list_archives(str(archive_dir))
    assert result == [p1, p2, p3]


def test_list_archives_empty_dir(archive_dir):
    assert list_archives(str(archive_dir)) == []


def test_list_archives_missing_dir():
    assert list_archives("/nonexistent/path/xyz") == []


def test_apply_retention_keep_last(archive_dir):
    now = datetime(2024, 6, 1, 12, 0, 0)
    paths = [_make_archive(archive_dir, now - timedelta(days=i)) for i in range(4, -1, -1)]
    policy = RetentionPolicy(keep_last=2)
    deleted = apply_retention(str(archive_dir), policy)
    remaining = list_archives(str(archive_dir))
    assert len(remaining) == 2
    assert len(deleted) == 3


def test_apply_retention_max_age(archive_dir):
    now = datetime.utcnow()
    old = _make_archive(archive_dir, now - timedelta(days=10))
    _make_archive(archive_dir, now - timedelta(days=1))
    policy = RetentionPolicy(max_age_days=5)
    deleted = apply_retention(str(archive_dir), policy)
    assert str(old) in deleted
    assert len(list_archives(str(archive_dir))) == 1


def test_apply_retention_combined(archive_dir):
    now = datetime.utcnow()
    _make_archive(archive_dir, now - timedelta(days=20))
    _make_archive(archive_dir, now - timedelta(days=15))
    _make_archive(archive_dir, now - timedelta(hours=2))
    _make_archive(archive_dir, now - timedelta(hours=1))
    policy = RetentionPolicy(keep_last=1, max_age_days=10)
    deleted = apply_retention(str(archive_dir), policy)
    assert len(list_archives(str(archive_dir))) == 1
    assert len(deleted) == 3


def test_apply_retention_no_policy_no_deletion(archive_dir):
    now = datetime.utcnow()
    for i in range(3):
        _make_archive(archive_dir, now - timedelta(days=i))
    deleted = apply_retention(str(archive_dir), RetentionPolicy())
    assert deleted == []
    assert len(list_archives(str(archive_dir))) == 3
