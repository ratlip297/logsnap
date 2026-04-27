"""Tests for logsnap.exporter and logsnap.cli_export."""
from __future__ import annotations

import csv
import io
import json
import tarfile
from pathlib import Path

import pytest

from logsnap.exporter import ExportOptions, export_archive, write_export
from logsnap.cli_export import build_export_parser, export_options_from_args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_archive(tmp_path: Path, entries: dict[str, list[str]]) -> Path:
    """Create a minimal .tar.gz archive with one file per service."""
    archive = tmp_path / "snap_20240101_120000.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for service, lines in entries.items():
            data = "\n".join(lines).encode()
            info = tarfile.TarInfo(name=f"{service}.log")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return archive


@pytest.fixture()
def simple_archive(tmp_path: Path) -> Path:
    return _make_archive(
        tmp_path,
        {
            "web": ["INFO started", "ERROR boom"],
            "worker": ["DEBUG polling"],
        },
    )


# ---------------------------------------------------------------------------
# exporter.export_archive
# ---------------------------------------------------------------------------

def test_export_json_returns_valid_json(simple_archive: Path) -> None:
    result = export_archive(simple_archive)
    parsed = json.loads(result)
    assert "entries" in parsed
    assert "metadata" in parsed


def test_export_json_entry_count(simple_archive: Path) -> None:
    parsed = json.loads(export_archive(simple_archive))
    assert parsed["metadata"]["total_lines"] == 3
    assert len(parsed["entries"]) == 3


def test_export_json_no_metadata(simple_archive: Path) -> None:
    opts = ExportOptions(include_metadata=False)
    parsed = json.loads(export_archive(simple_archive, opts))
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_export_csv_returns_valid_csv(simple_archive: Path) -> None:
    opts = ExportOptions(format="csv")
    result = export_archive(simple_archive, opts)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 3
    assert set(reader.fieldnames or []) == {"service", "line", "text"}


def test_export_csv_service_names(simple_archive: Path) -> None:
    opts = ExportOptions(format="csv")
    reader = csv.DictReader(io.StringIO(export_archive(simple_archive, opts)))
    services = {row["service"] for row in reader}
    assert services == {"web", "worker"}


def test_export_unsupported_format_raises(simple_archive: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        export_archive(simple_archive, ExportOptions(format="xml"))  # type: ignore[arg-type]


def test_write_export_creates_file(simple_archive: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.json"
    returned = write_export(simple_archive, dest)
    assert returned == dest
    assert dest.exists()
    json.loads(dest.read_text())


# ---------------------------------------------------------------------------
# cli_export helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser():
    return build_export_parser()


def test_defaults(parser, simple_archive: Path) -> None:
    args = parser.parse_args([str(simple_archive)])
    opts = export_options_from_args(args)
    assert opts.format == "json"
    assert opts.pretty is True
    assert opts.include_metadata is True


def test_csv_flag(parser, simple_archive: Path) -> None:
    args = parser.parse_args([str(simple_archive), "--format", "csv"])
    opts = export_options_from_args(args)
    assert opts.format == "csv"


def test_no_pretty_flag(parser, simple_archive: Path) -> None:
    args = parser.parse_args([str(simple_archive), "--no-pretty"])
    opts = export_options_from_args(args)
    assert opts.pretty is False


def test_no_metadata_flag(parser, simple_archive: Path) -> None:
    args = parser.parse_args([str(simple_archive), "--no-metadata"])
    opts = export_options_from_args(args)
    assert opts.include_metadata is False
