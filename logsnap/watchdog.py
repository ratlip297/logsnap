"""Watch a log archive directory and alert when size or count thresholds are exceeded."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from logsnap.retention import list_archives


@dataclass
class WatchdogConfig:
    archive_dir: str
    max_total_size_mb: Optional[float] = None
    max_archive_count: Optional[int] = None


@dataclass
class WatchdogAlert:
    kind: str  # "size" or "count"
    message: str


@dataclass
class WatchdogReport:
    archive_dir: str
    total_size_bytes: int
    archive_count: int
    alerts: List[WatchdogAlert] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.alerts) == 0

    @property
    def total_size_mb(self) -> float:
        return self.total_size_bytes / (1024 * 1024)

    def summary(self) -> str:
        lines = [
            f"Directory : {self.archive_dir}",
            f"Archives  : {self.archive_count}",
            f"Total size: {self.total_size_mb:.2f} MB",
        ]
        if self.ok:
            lines.append("Status    : OK")
        else:
            lines.append(f"Status    : {len(self.alerts)} alert(s)")
            for alert in self.alerts:
                lines.append(f"  [{alert.kind.upper()}] {alert.message}")
        return "\n".join(lines)


def _total_size(paths: List[Path]) -> int:
    total = 0
    for p in paths:
        try:
            total += p.stat().st_size
        except OSError:
            pass
    return total


def run_watchdog(cfg: WatchdogConfig) -> WatchdogReport:
    """Inspect the archive directory and return a WatchdogReport."""
    archives = list_archives(cfg.archive_dir)
    count = len(archives)
    size_bytes = _total_size(archives)

    alerts: List[WatchdogAlert] = []

    if cfg.max_archive_count is not None and count > cfg.max_archive_count:
        alerts.append(
            WatchdogAlert(
                kind="count",
                message=(
                    f"{count} archives found, limit is {cfg.max_archive_count}"
                ),
            )
        )

    if cfg.max_total_size_mb is not None:
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > cfg.max_total_size_mb:
            alerts.append(
                WatchdogAlert(
                    kind="size",
                    message=(
                        f"{size_mb:.2f} MB used, limit is {cfg.max_total_size_mb} MB"
                    ),
                )
            )

    return WatchdogReport(
        archive_dir=cfg.archive_dir,
        total_size_bytes=size_bytes,
        archive_count=count,
        alerts=alerts,
    )
