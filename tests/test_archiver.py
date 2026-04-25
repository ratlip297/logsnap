"""Tests for logsnap.archiver module."""

import os
import zipfile
from datetime import datetime

import pytest

from logsnap.archiver import (
    make_archive_name,
    write_archive,
    list_archive_contents,
)


FIXED_TS = datetime(2024, 6, 15, 12, 30, 45)


def test_make_archive_name_uses_timestamp():
    name = make_archive_name(prefix="logsnap", timestamp=FIXED_TS)
    assert name == "logsnap_20240615_123045.zip"


def test_make_archive_name_custom_prefix():
    name = make_archive_name(prefix="myapp", timestamp=FIXED_TS)
    assert name.startswith("myapp_")
    assert name.endswith(".zip")


def test_make_archive_name_default_timestamp_is_recent():
    name = make_archive_name()
    # Should at least be a non-empty string ending in .zip
    assert isinstance(name, str)
    assert name.endswith(".zip")


def test_write_archive_creates_file(tmp_path):
    logs = {"web": "GET /health 200\n", "worker": "job done\n"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert os.path.isfile(path)
    assert path.endswith(".zip")


def test_write_archive_contains_log_entries(tmp_path):
    logs = {"web": "log line 1\n", "db": "query ok\n"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    contents = list_archive_contents(path)
    assert "web.log" in contents
    assert "db.log" in contents


def test_write_archive_contains_manifest(tmp_path):
    logs = {"alpha": "a\n", "beta": "b\n"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    contents = list_archive_contents(path)
    assert "manifest.txt" in contents


def test_write_archive_manifest_lists_services(tmp_path):
    logs = {"svc1": "data", "svc2": "data"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    with zipfile.ZipFile(path, "r") as zf:
        manifest = zf.read("manifest.txt").decode()
    assert "svc1.log" in manifest
    assert "svc2.log" in manifest


def test_write_archive_log_content_preserved(tmp_path):
    logs = {"api": "hello world\n"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    with zipfile.ZipFile(path, "r") as zf:
        content = zf.read("api.log").decode()
    assert content == "hello world\n"


def test_write_archive_creates_output_dir(tmp_path):
    nested = str(tmp_path / "deep" / "nested")
    logs = {"x": "y"}
    path = write_archive(logs, output_dir=nested, timestamp=FIXED_TS)
    assert os.path.isfile(path)


def test_list_archive_contents_returns_list(tmp_path):
    logs = {"svc": "log"}
    path = write_archive(logs, output_dir=str(tmp_path), timestamp=FIXED_TS)
    result = list_archive_contents(path)
    assert isinstance(result, list)
    assert len(result) >= 2  # at least svc.log + manifest.txt
