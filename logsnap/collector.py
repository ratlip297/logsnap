"""Log collection from configured services."""

import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from logsnap.config import ServiceConfig, SnapConfig


def collect_service_logs(
    service: ServiceConfig,
    since: Optional[str] = None,
    lines: Optional[int] = None,
) -> str:
    """Fetch logs for a single service using journalctl or a custom command."""
    if service.command:
        cmd = service.command
    elif shutil.which("journalctl"):
        cmd = f"journalctl -u {service.name} --no-pager"
        if since:
            cmd += f" --since '{since}'"
        if lines:
            cmd += f" -n {lines}"
    else:
        raise RuntimeError(
            f"No command configured for service '{service.name}' and journalctl not found."
        )

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Log collection failed for '{service.name}': {result.stderr.strip()}"
        )

    return result.stdout


def collect_all(
    config: SnapConfig,
    output_dir: Path,
    since: Optional[str] = None,
) -> dict[str, Path]:
    """Collect logs from all services and write them to output_dir.

    Returns a mapping of service name -> written log file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    written: dict[str, Path] = {}

    for service in config.services:
        try:
            logs = collect_service_logs(
                service,
                since=since,
                lines=config.default_lines,
            )
        except RuntimeError as exc:
            print(f"[warn] Skipping '{service.name}': {exc}")
            continue

        log_file = output_dir / f"{service.name}_{timestamp}.log"
        log_file.write_text(logs, encoding="utf-8")
        written[service.name] = log_file
        print(f"[ok] Collected '{service.name}' -> {log_file}")

    return written
