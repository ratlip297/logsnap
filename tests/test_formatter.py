"""Tests for logsnap.formatter."""

import pytest
from logsnap.snapshot import SnapshotResult
from logsnap.formatter import FormatOptions, format_result, format_summary_line


@pytest.fixture
def ok_result():
    return SnapshotResult(
        success=True,
        archive_path="/tmp/logsnap_20240101_120000.tar.gz",
        logs={"web": ["line1", "line2"], "db": ["line3"]},
        errors={},
        services_ok=2,
    )


@pytest.fixture
def partial_result():
    return SnapshotResult(
        success=False,
        archive_path="/tmp/logsnap_20240101_120000.tar.gz",
        logs={"web": ["line1"]},
        errors={"db": "connection refused"},
        services_ok=1,
    )


def test_format_result_success_contains_status(ok_result):
    output = format_result(ok_result, FormatOptions(color=False))
    assert "SUCCESS" in output


def test_format_result_shows_archive_path(ok_result):
    output = format_result(ok_result, FormatOptions(color=False))
    assert ok_result.archive_path in output


def test_format_result_hides_archive_when_disabled(ok_result):
    output = format_result(ok_result, FormatOptions(color=False, show_archive_path=False))
    assert ok_result.archive_path not in output


def test_format_result_verbose_shows_service_lines(ok_result):
    output = format_result(ok_result, FormatOptions(color=False, verbose=True))
    assert "web" in output
    assert "db" in output
    assert "2 line(s)" in output


def test_format_result_partial_shows_errors(partial_result):
    output = format_result(partial_result, FormatOptions(color=False))
    assert "PARTIAL" in output
    assert "connection refused" in output
    assert "db" in output


def test_format_result_services_count(ok_result):
    output = format_result(ok_result, FormatOptions(color=False))
    assert "2 ok" in output
    assert "0 failed" in output


def test_format_summary_line_ok(ok_result):
    line = format_summary_line(ok_result)
    assert "status=ok" in line
    assert "services_ok=2" in line
    assert "errors=0" in line
    assert ok_result.archive_path in line


def test_format_summary_line_partial(partial_result):
    line = format_summary_line(partial_result)
    assert "status=partial" in line
    assert "errors=1" in line


def test_format_result_no_archive_path():
    result = SnapshotResult(
        success=False,
        archive_path=None,
        logs={},
        errors={"svc": "failed"},
        services_ok=0,
    )
    output = format_result(result, FormatOptions(color=False))
    assert "PARTIAL" in output or "FAILED" in output
