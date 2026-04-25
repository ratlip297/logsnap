"""High-level snapshot orchestration: collect -> filter -> archive."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from logsnap.config import SnapConfig
from logsnap.collector import collect_all
from logsnap.archiver import write_archive

logger = logging.getLogger(__name__)


@dataclass
class SnapshotResult:
    archive_path: str
    services_captured: list = field(default_factory=list)
    services_failed: list = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def success(self) -> bool:
        return len(self.services_captured) > 0

    def summary(self) -> str:
        ok = len(self.services_captured)
        fail = len(self.services_failed)
        return (
            f"Snapshot: {self.archive_path}\n"
            f"  Captured : {ok} service(s): {', '.join(self.services_captured)}\n"
            f"  Failed   : {fail} service(s): {', '.join(self.services_failed)}"
        )


def run_snapshot(
    config: SnapConfig,
    output_dir: str = "./snapshots",
    timestamp: Optional[datetime] = None,
) -> SnapshotResult:
    """
    Collect logs from all configured services and write them to an archive.

    Args:
        config: Loaded SnapConfig with service definitions.
        output_dir: Where to write the resulting zip archive.
        timestamp: Optional fixed timestamp (useful for tests).

    Returns:
        SnapshotResult with archive path and per-service status.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    logger.info("Starting snapshot for %d service(s).", len(config.services))

    raw_results = collect_all(config)

    logs: dict = {}
    captured = []
    failed = []

    for service_name, result in raw_results.items():
        if result.get("error"):
            logger.warning("Service %s failed: %s", service_name, result["error"])
            failed.append(service_name)
        else:
            logs[service_name] = result.get("output", "")
            captured.append(service_name)

    archive_path = write_archive(
        logs=logs,
        output_dir=output_dir,
        timestamp=timestamp,
    )

    logger.info("Archive written to %s", archive_path)

    return SnapshotResult(
        archive_path=archive_path,
        services_captured=captured,
        services_failed=failed,
        timestamp=timestamp,
    )
