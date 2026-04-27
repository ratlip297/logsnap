"""Compare two logsnap archives and report differences in log entries."""

from __future__ import annotations

import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class DiffResult:
    archive_a: str
    archive_b: str
    added_services: List[str] = field(default_factory=list)
    removed_services: List[str] = field(default_factory=list)
    changed_services: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # name -> (lines_a, lines_b)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_services or self.removed_services or self.changed_services)

    def summary(self) -> str:
        lines = [
            f"Diff: {self.archive_a}  →  {self.archive_b}",
        ]
        if self.added_services:
            lines.append(f"  + added services:   {', '.join(self.added_services)}")
        if self.removed_services:
            lines.append(f"  - removed services: {', '.join(self.removed_services)}")
        for svc, (cnt_a, cnt_b) in self.changed_services.items():
            delta = cnt_b - cnt_a
            sign = "+" if delta >= 0 else ""
            lines.append(f"  ~ {svc}: {cnt_a} → {cnt_b} lines ({sign}{delta})")
        if not self.has_changes:
            lines.append("  (no differences)")
        return "\n".join(lines)


def _read_service_line_counts(archive_path: Path) -> Dict[str, int]:
    """Return a mapping of service name to line count from a logsnap tar.gz archive."""
    counts: Dict[str, int] = {}
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            name = Path(member.name).stem  # strip .log extension
            f = tar.extractfile(member)
            if f is None:
                continue
            content = f.read().decode("utf-8", errors="replace")
            counts[name] = len([l for l in content.splitlines() if l.strip()])
    return counts


def diff_archives(path_a: Path | str, path_b: Path | str) -> DiffResult:
    """Compare two archives and return a DiffResult describing the differences."""
    path_a = Path(path_a)
    path_b = Path(path_b)

    counts_a = _read_service_line_counts(path_a)
    counts_b = _read_service_line_counts(path_b)

    services_a: Set[str] = set(counts_a)
    services_b: Set[str] = set(counts_b)

    result = DiffResult(
        archive_a=path_a.name,
        archive_b=path_b.name,
        added_services=sorted(services_b - services_a),
        removed_services=sorted(services_a - services_b),
    )

    for svc in sorted(services_a & services_b):
        if counts_a[svc] != counts_b[svc]:
            result.changed_services[svc] = (counts_a[svc], counts_b[svc])

    return result
