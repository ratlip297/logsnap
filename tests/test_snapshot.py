"""Tests for logsnap.snapshot module."""

import os
from datetime import datetime
from unittest.mock import patch

import pytest

from logsnap.config import SnapConfig, ServiceConfig
from logsnap.snapshot import run_snapshot, SnapshotResult


FIXED_TS = datetime(2024, 6, 15, 9, 0, 0)


@pytest.fixture
def two_service_config():
    return SnapConfig(
        services=[
            ServiceConfig(name="api", command="journalctl -u api"),
            ServiceConfig(name="worker", command="journalctl -u worker"),
        ]
    )


def _fake_collect_all_ok(config):
    return {
        svc.name: {"output": f"logs for {svc.name}", "error": None}
        for svc in config.services
    }


def _fake_collect_all_partial(config):
    results = {}
    for i, svc in enumerate(config.services):
        if i == 0:
            results[svc.name] = {"output": f"logs for {svc.name}", "error": None}
        else:
            results[svc.name] = {"output": "", "error": "exit code 1"}
    return results


def test_run_snapshot_returns_result(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_ok):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert isinstance(result, SnapshotResult)


def test_run_snapshot_archive_exists(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_ok):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert os.path.isfile(result.archive_path)


def test_run_snapshot_all_captured(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_ok):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert set(result.services_captured) == {"api", "worker"}
    assert result.services_failed == []


def test_run_snapshot_partial_failure(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_partial):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert len(result.services_captured) == 1
    assert len(result.services_failed) == 1


def test_snapshot_result_success_true(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_ok):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert result.success is True


def test_snapshot_result_success_false_when_all_fail(tmp_path, two_service_config):
    def all_fail(config):
        return {svc.name: {"output": "", "error": "boom"} for svc in config.services}

    with patch("logsnap.snapshot.collect_all", side_effect=all_fail):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    assert result.success is False


def test_snapshot_summary_contains_archive_path(tmp_path, two_service_config):
    with patch("logsnap.snapshot.collect_all", side_effect=_fake_collect_all_ok):
        result = run_snapshot(two_service_config, output_dir=str(tmp_path), timestamp=FIXED_TS)
    summary = result.summary()
    assert result.archive_path in summary
    assert "api" in summary
