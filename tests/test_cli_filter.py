"""Tests for logsnap.cli_filter."""

import pytest
from logsnap.cli_filter import (
    add_filter_args,
    filter_config_from_args,
    build_filter_parser,
)
from logsnap.filter import FilterConfig


@pytest.fixture()
def parser():
    return build_filter_parser()


def test_defaults_produce_empty_filter_config(parser):
    args = parser.parse_args([])
    cfg = filter_config_from_args(args)
    assert cfg.include_patterns == []
    assert cfg.exclude_patterns == []
    assert cfg.min_level is None


def test_single_include_pattern(parser):
    args = parser.parse_args(["--include", "ERROR"])
    cfg = filter_config_from_args(args)
    assert cfg.include_patterns == ["ERROR"]


def test_multiple_include_patterns(parser):
    args = parser.parse_args(["--include", "ERROR", "--include", "WARN"])
    cfg = filter_config_from_args(args)
    assert cfg.include_patterns == ["ERROR", "WARN"]


def test_exclude_pattern(parser):
    args = parser.parse_args(["--exclude", "healthcheck"])
    cfg = filter_config_from_args(args)
    assert cfg.exclude_patterns == ["healthcheck"]


def test_min_level_flag(parser):
    args = parser.parse_args(["--level", "warning"])
    cfg = filter_config_from_args(args)
    assert cfg.min_level == "warning"


def test_invalid_level_raises(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["--level", "verbose"])


def test_combined_flags(parser):
    args = parser.parse_args(
        ["--include", r"\bERROR\b", "--exclude", "noisy", "--level", "error"]
    )
    cfg = filter_config_from_args(args)
    assert cfg.include_patterns == [r"\bERROR\b"]
    assert cfg.exclude_patterns == ["noisy"]
    assert cfg.min_level == "error"


def test_filter_config_from_args_returns_filter_config_instance(parser):
    args = parser.parse_args([])
    assert isinstance(filter_config_from_args(args), FilterConfig)
