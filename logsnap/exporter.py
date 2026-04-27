"""Export snapshot archives to various output formats (JSON, CSV)."""
from __future__ import annotations

import csv
import io
import json
import tarfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ExportOptions:
    format: str = "json"  # "json" or "csv"
    pretty: bool = True
    include_metadata: bool = True


def _read_archive_entries(archive_path: Path) -> List[dict]:
    """Read all log entries from a .tar.gz archive into a list of dicts."""
    entries = []
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            lines = f.read().decode("utf-8", errors="replace").splitlines()
            for lineno, line in enumerate(lines, start=1):
                entries.append(
                    {
                        "service": Path(member.name).stem,
                        "line": lineno,
                        "text": line,
                    }
                )
    return entries


def export_archive(
    archive_path: Path,
    options: Optional[ExportOptions] = None,
) -> str:
    """Return archive contents serialised as JSON or CSV string."""
    if options is None:
        options = ExportOptions()

    entries = _read_archive_entries(archive_path)

    metadata = {}
    if options.include_metadata:
        metadata = {
            "archive": archive_path.name,
            "total_lines": len(entries),
        }

    if options.format == "json":
        payload = {"metadata": metadata, "entries": entries} if options.include_metadata else entries
        indent = 2 if options.pretty else None
        return json.dumps(payload, indent=indent)

    if options.format == "csv":
        buf = io.StringIO()
        fieldnames = ["service", "line", "text"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
        return buf.getvalue()

    raise ValueError(f"Unsupported export format: {options.format!r}")


def write_export(archive_path: Path, dest: Path, options: Optional[ExportOptions] = None) -> Path:
    """Write exported content to *dest* and return the path."""
    content = export_archive(archive_path, options)
    dest.write_text(content, encoding="utf-8")
    return dest
