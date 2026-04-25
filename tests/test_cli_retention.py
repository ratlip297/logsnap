"""Tests for logsnap.cli_retention."""

import pytest
from unittest.mock import patch, MagicMock
from logsnap.cli_retention import (
    build_retention_parser,
    retention_policy_from_args,
    run_retention_command,
)
from logsnap.retention import RetentionPolicy


@pytest.fixture
def parser():
    return build_retention_parser()


def test_defaults_produce_no_limits(parser):
    args = parser.parse_args(["/some/dir"])
    policy = retention_policy_from_args(args)
    assert policy.max_archives is None
    assert policy.max_age_days is None


def test_max_archives_parsed(parser):
    args = parser.parse_args(["--max-archives", "5", "/some/dir"])
    policy = retention_policy_from_args(args)
    assert policy.max_archives == 5


def test_max_age_days_parsed(parser):
    args = parser.parse_args(["--max-age-days", "30", "/some/dir"])
    policy = retention_policy_from_args(args)
    assert policy.max_age_days == 30.0


def test_dry_run_flag(parser):
    args = parser.parse_args(["--dry-run", "/some/dir"])
    assert args.dry_run is True


def test_dry_run_default_false(parser):
    args = parser.parse_args(["/some/dir"])
    assert args.dry_run is False


def test_run_retention_no_archives(parser, capsys):
    args = parser.parse_args(["/empty/dir"])
    with patch("logsnap.cli_retention.list_archives", return_value=[]):
        code = run_retention_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "No archives found" in captured.out


def test_run_retention_deletes_and_reports(parser, capsys):
    args = parser.parse_args(["--max-archives", "2", "/some/dir"])
    fake_archives = ["/some/dir/a.tar.gz", "/some/dir/b.tar.gz", "/some/dir/c.tar.gz"]
    deleted = ["/some/dir/a.tar.gz"]
    with patch("logsnap.cli_retention.list_archives", return_value=fake_archives), \
         patch("logsnap.cli_retention.apply_retention", return_value=deleted):
        code = run_retention_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "a.tar.gz" in captured.out
    assert "Deleted 1 archive(s)" in captured.out


def test_run_retention_dry_run_prefix(parser, capsys):
    args = parser.parse_args(["--dry-run", "--max-archives", "1", "/some/dir"])
    fake_archives = ["/some/dir/old.tar.gz", "/some/dir/new.tar.gz"]
    deleted = ["/some/dir/old.tar.gz"]
    with patch("logsnap.cli_retention.list_archives", return_value=fake_archives), \
         patch("logsnap.cli_retention.apply_retention", return_value=deleted):
        code = run_retention_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out
    assert "old.tar.gz" in captured.out


def test_run_retention_nothing_removed(parser, capsys):
    args = parser.parse_args(["/some/dir"])
    fake_archives = ["/some/dir/only.tar.gz"]
    with patch("logsnap.cli_retention.list_archives", return_value=fake_archives), \
         patch("logsnap.cli_retention.apply_retention", return_value=[]):
        code = run_retention_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "No archives removed" in captured.out
