"""Live log tailing — stream last N lines from a service log file or command."""

from __future__ import annotations

import subprocess
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

from logsnap.config import ServiceConfig
from logsnap.filter import FilterConfig, matches


@dataclass
class TailOptions:
    lines: int = 20
    follow: bool = False
    filter_config: FilterConfig = field(default_factory=FilterConfig)


def _tail_file(path: Path, n: int) -> List[str]:
    """Return the last *n* lines from a file without reading it all into memory."""
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    with path.open("r", errors="replace") as fh:
        return list(deque(fh, maxlen=n))


def _tail_command(cmd: str, n: int) -> List[str]:
    """Run *cmd* and return the last *n* lines of its stdout."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command exited with code {result.returncode}: {result.stderr.strip()}"
        )
    all_lines = result.stdout.splitlines(keepends=True)
    return list(deque(all_lines, maxlen=n))


def tail_service(
    service: ServiceConfig,
    options: TailOptions,
) -> List[str]:
    """Fetch the last N lines for *service*, applying any filter."""
    if service.command:
        raw = _tail_command(service.command, options.lines)
    elif service.log_path:
        raw = _tail_file(Path(service.log_path), options.lines)
    else:
        raise ValueError(f"Service '{service.name}' has no command or log_path.")

    return [line for line in raw if matches(line.rstrip("\n"), options.filter_config)]


def stream_service(service: ServiceConfig, filter_config: FilterConfig) -> Iterator[str]:
    """Yield lines continuously from *service* using `tail -f` semantics.

    Only works when the service has a *log_path*.
    """
    if not service.log_path:
        raise ValueError(f"Service '{service.name}' has no log_path for streaming.")
    path = Path(service.log_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    with path.open("r", errors="replace") as fh:
        fh.seek(0, 2)  # seek to end
        while True:
            line = fh.readline()
            if line:
                stripped = line.rstrip("\n")
                if matches(stripped, filter_config):
                    yield stripped
