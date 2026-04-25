"""Archive collected logs into a timestamped zip archive."""

import zipfile
import os
from datetime import datetime
from pathlib import Path
from typing import Dict


DEFAULT_OUTPUT_DIR = "./snapshots"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def make_archive_name(prefix: str = "logsnap", timestamp: datetime = None) -> str:
    """Generate a timestamped archive filename."""
    if timestamp is None:
        timestamp = datetime.utcnow()
    ts = timestamp.strftime(TIMESTAMP_FORMAT)
    return f"{prefix}_{ts}.zip"


def write_archive(
    logs: Dict[str, str],
    output_dir: str = DEFAULT_OUTPUT_DIR,
    prefix: str = "logsnap",
    timestamp: datetime = None,
) -> str:
    """
    Write collected logs into a zip archive.

    Args:
        logs: Mapping of service name -> log content.
        output_dir: Directory to write the archive into.
        prefix: Archive filename prefix.
        timestamp: Optional fixed timestamp (useful for tests).

    Returns:
        Absolute path to the created archive.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    archive_name = make_archive_name(prefix=prefix, timestamp=timestamp)
    archive_path = os.path.join(output_dir, archive_name)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for service_name, content in logs.items():
            entry_name = f"{service_name}.log"
            zf.writestr(entry_name, content)
        # Write a small manifest
        manifest_lines = [f"{name}.log" for name in sorted(logs.keys())]
        zf.writestr("manifest.txt", "\n".join(manifest_lines) + "\n")

    return os.path.abspath(archive_path)


def list_archive_contents(archive_path: str) -> list:
    """Return list of filenames inside the archive."""
    with zipfile.ZipFile(archive_path, "r") as zf:
        return zf.namelist()
