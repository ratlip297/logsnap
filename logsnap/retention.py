"""Retention policy: prune old snapshot archives based on count or age."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


ARCHIVE_TIMESTAMP_RE = re.compile(r"(\d{8}T\d{6})")


@dataclass
class RetentionPolicy:
    keep_last: Optional[int] = None  # keep N most recent archives
    max_age_days: Optional[int] = None  # delete archives older than N days


def _parse_timestamp(path: Path) -> Optional[datetime]:
    """Extract datetime from archive filename, or None if not parseable."""
    m = ARCHIVE_TIMESTAMP_RE.search(path.name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
    except ValueError:
        return None


def list_archives(directory: str, prefix: str = "logsnap") -> List[Path]:
    """Return archive files in *directory* matching the given prefix, sorted oldest-first."""
    d = Path(directory)
    if not d.is_dir():
        return []
    archives = [
        p for p in d.iterdir()
        if p.is_file() and p.name.startswith(prefix) and p.suffix == ".tar.gz"
    ]
    archives.sort(key=lambda p: _parse_timestamp(p) or datetime.min)
    return archives


def apply_retention(directory: str, policy: RetentionPolicy, prefix: str = "logsnap") -> List[str]:
    """Delete archives that violate *policy*. Returns list of deleted file paths."""
    archives = list_archives(directory, prefix=prefix)
    to_delete: set[Path] = set()

    if policy.max_age_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=policy.max_age_days)
        for p in archives:
            ts = _parse_timestamp(p)
            if ts is not None and ts < cutoff:
                to_delete.add(p)

    if policy.keep_last is not None:
        eligible = [p for p in archives if p not in to_delete]
        excess = len(eligible) - policy.keep_last
        if excess > 0:
            to_delete.update(eligible[:excess])

    deleted: List[str] = []
    for p in to_delete:
        try:
            os.remove(p)
            deleted.append(str(p))
        except OSError:
            pass
    return sorted(deleted)
