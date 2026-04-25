"""Format snapshot results for CLI output."""

from dataclasses import dataclass
from typing import Optional
from logsnap.snapshot import SnapshotResult


@dataclass
class FormatOptions:
    verbose: bool = False
    show_archive_path: bool = True
    color: bool = True


ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, code: str, enabled: bool = True) -> str:
    if not enabled:
        return text
    return f"{code}{text}{ANSI_RESET}"


def format_result(result: SnapshotResult, options: Optional[FormatOptions] = None) -> str:
    """Render a SnapshotResult as a human-readable string."""
    if options is None:
        options = FormatOptions()

    lines = []

    status_label = "SUCCESS" if result.success else "PARTIAL" if result.errors else "FAILED"
    color = ANSI_GREEN if result.success else ANSI_YELLOW if result.errors else ANSI_RED
    lines.append(_colorize(f"[{status_label}] Snapshot complete", ANSI_BOLD if options.color else "", options.color))

    if options.show_archive_path and result.archive_path:
        lines.append(f"  Archive : {result.archive_path}")

    lines.append(f"  Services: {result.services_ok} ok, {len(result.errors)} failed")

    if options.verbose:
        for svc, log_lines in result.logs.items():
            label = _colorize(svc, ANSI_GREEN, options.color) if svc not in result.errors else _colorize(svc, ANSI_RED, options.color)
            lines.append(f"  [{label}] {len(log_lines)} line(s)")

    if result.errors:
        lines.append(_colorize("  Errors:", ANSI_RED, options.color))
        for svc, msg in result.errors.items():
            lines.append(f"    {svc}: {msg}")

    return "\n".join(lines)


def format_summary_line(result: SnapshotResult) -> str:
    """Return a single-line summary suitable for logging."""
    status = "ok" if result.success else "partial" if result.errors else "failed"
    archive = result.archive_path or "<no archive>"
    return f"snapshot status={status} services_ok={result.services_ok} errors={len(result.errors)} archive={archive}"
