"""Tests for logsnap.summarizer."""

import pytest

from logsnap.summarizer import (
    ServiceSummary,
    SnapSummary,
    _count_levels,
    _top_patterns,
    summarize_logs,
    format_snap_summary,
)


SAMPLE_LINES = [
    "2024-01-01 INFO  Starting application",
    "2024-01-01 DEBUG Loading config",
    "2024-01-01 INFO  Connected to database",
    "2024-01-01 WARNING Slow query detected",
    "2024-01-01 ERROR  Failed to reach endpoint",
    "2024-01-01 INFO  Request processed",
]


def test_count_levels_basic():
    counts = _count_levels(SAMPLE_LINES)
    assert counts.get("info", 0) == 3
    assert counts.get("debug", 0) == 1
    assert counts.get("warning", 0) == 1
    assert counts.get("error", 0) == 1


def test_count_levels_empty():
    assert _count_levels([]) == {}


def test_count_levels_unknown_level():
    counts = _count_levels(["just some random text without level"])
    assert "unknown" in counts


def test_top_patterns_returns_list():
    patterns = _top_patterns(SAMPLE_LINES, n=3)
    assert isinstance(patterns, list)
    assert len(patterns) <= 3


def test_top_patterns_empty_lines():
    assert _top_patterns([]) == []


def test_top_patterns_skips_level_words():
    lines = ["INFO INFO INFO ERROR DEBUG application started"]
    patterns = _top_patterns(lines, n=5)
    upper_patterns = [p.upper() for p in patterns]
    assert "INFO" not in upper_patterns
    assert "ERROR" not in upper_patterns


def test_summarize_logs_single_service():
    log_map = {"web": SAMPLE_LINES}
    snap = summarize_logs(log_map)
    assert snap.service_count == 1
    assert snap.total_lines == len(SAMPLE_LINES)
    assert snap.services[0].service == "web"


def test_summarize_logs_multiple_services():
    log_map = {
        "web": SAMPLE_LINES,
        "worker": ["INFO job started", "ERROR job failed"],
    }
    snap = summarize_logs(log_map)
    assert snap.service_count == 2
    assert snap.total_lines == len(SAMPLE_LINES) + 2


def test_summarize_logs_empty():
    snap = summarize_logs({})
    assert snap.service_count == 0
    assert snap.total_lines == 0


def test_format_snap_summary_contains_service_name():
    snap = summarize_logs({"api": SAMPLE_LINES})
    output = format_snap_summary(snap)
    assert "api" in output
    assert "6 lines" in output


def test_format_snap_summary_shows_totals():
    snap = summarize_logs({"svc1": ["INFO a", "ERROR b"], "svc2": ["DEBUG c"]})
    output = format_snap_summary(snap)
    assert "2 service(s)" in output
    assert "3 total lines" in output


def test_format_snap_summary_no_services():
    snap = SnapSummary(services=[])
    output = format_snap_summary(snap)
    assert "0 service(s)" in output
