"""Tests for logsnap.filter."""

import pytest
from logsnap.filter import FilterConfig, apply_filter, _detect_level


SAMPLE_LINES = [
    "2024-01-01 DEBUG starting up",
    "2024-01-01 INFO service ready",
    "2024-01-01 WARNING disk space low",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 CRITICAL system failure",
    "2024-01-01 INFO health check ok",
]


def test_no_filters_returns_all_lines():
    cfg = FilterConfig()
    assert apply_filter(SAMPLE_LINES, cfg) == SAMPLE_LINES


def test_include_pattern_filters_correctly():
    cfg = FilterConfig(include_patterns=[r"ERROR|CRITICAL"])
    result = apply_filter(SAMPLE_LINES, cfg)
    assert len(result) == 2
    assert all("ERROR" in r or "CRITICAL" in r for r in result)


def test_exclude_pattern_removes_lines():
    cfg = FilterConfig(exclude_patterns=[r"health check"])
    result = apply_filter(SAMPLE_LINES, cfg)
    assert not any("health check" in r for r in result)
    assert len(result) == len(SAMPLE_LINES) - 1


def test_min_level_warning_excludes_debug_and_info():
    cfg = FilterConfig(min_level="warning")
    result = apply_filter(SAMPLE_LINES, cfg)
    for line in result:
        assert not ("DEBUG" in line or ("INFO" in line and "health" not in line and "ready" not in line))
    # WARNING, ERROR, CRITICAL + lines without a detectable level should pass
    assert any("WARNING" in r for r in result)
    assert any("ERROR" in r for r in result)
    assert any("CRITICAL" in r for r in result)


def test_min_level_error_keeps_only_error_and_critical():
    cfg = FilterConfig(min_level="error")
    result = apply_filter(SAMPLE_LINES, cfg)
    assert all("ERROR" in r or "CRITICAL" in r for r in result)


def test_exclude_takes_precedence_over_include():
    cfg = FilterConfig(include_patterns=[r"INFO"], exclude_patterns=[r"health check"])
    result = apply_filter(SAMPLE_LINES, cfg)
    assert not any("health check" in r for r in result)
    assert all("INFO" in r for r in result)


def test_detect_level_known_levels():
    assert _detect_level("INFO service started") == "info"
    assert _detect_level("[ERROR] boom") == "error"
    assert _detect_level("no level here") is None


def test_filter_config_matches_plain_line_no_level():
    cfg = FilterConfig(min_level="error")
    # Line with no detectable level should pass through
    assert cfg.matches("plain log line without level") is True
