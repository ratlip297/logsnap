"""Deduplicator: remove or count duplicate log lines within a snapshot archive."""

from __future__ import annotations

import tarfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class DeduplicationResult:
    service_name: str
    original_count: int
    unique_count: int
    duplicates_removed: int
    top_duplicates: List[Tuple[str, int]] = field(default_factory=list)

    @property
    def reduction_pct(self) -> float:
        if self.original_count == 0:
            return 0.0
        return round(100.0 * self.duplicates_removed / self.original_count, 1)

    def summary(self) -> str:
        return (
            f"{self.service_name}: {self.original_count} lines → "
            f"{self.unique_count} unique "
            f"(-{self.duplicates_removed}, {self.reduction_pct}% reduction)"
        )


def _read_lines(archive_path: Path, member_name: str) -> List[str]:
    """Extract and return lines for a single archive member."""
    with tarfile.open(archive_path, "r:gz") as tar:
        try:
            f = tar.extractfile(member_name)
        except KeyError:
            return []
        if f is None:
            return []
        return f.read().decode(errors="replace").splitlines()


def deduplicate_service(
    archive_path: Path,
    member_name: str,
    top_n: int = 5,
) -> DeduplicationResult:
    """Analyse duplicate lines for one service log member in the archive."""
    service_name = Path(member_name).stem
    lines = _read_lines(archive_path, member_name)
    counts: Counter[str] = Counter(lines)
    original = len(lines)
    unique = len(counts)
    removed = original - unique
    top = counts.most_common(top_n)
    # Only report lines that appear more than once
    top_dups = [(line, cnt) for line, cnt in top if cnt > 1]
    return DeduplicationResult(
        service_name=service_name,
        original_count=original,
        unique_count=unique,
        duplicates_removed=removed,
        top_duplicates=top_dups,
    )


def deduplicate_archive(
    archive_path: Path,
    top_n: int = 5,
) -> Dict[str, DeduplicationResult]:
    """Return deduplication results for every .log member in the archive."""
    results: Dict[str, DeduplicationResult] = {}
    with tarfile.open(archive_path, "r:gz") as tar:
        members = [m.name for m in tar.getmembers() if m.name.endswith(".log")]
    for member in members:
        result = deduplicate_service(archive_path, member, top_n=top_n)
        results[result.service_name] = result
    return results
