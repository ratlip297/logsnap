"""Summarize log content across services: line counts, level breakdown, top patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from logsnap.filter import _detect_level


@dataclass
class ServiceSummary:
    service: str
    total_lines: int = 0
    level_counts: Dict[str, int] = field(default_factory=dict)
    top_patterns: List[str] = field(default_factory=list)


@dataclass
class SnapSummary:
    services: List[ServiceSummary] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return sum(s.total_lines for s in self.services)

    @property
    def service_count(self) -> int:
        return len(self.services)


def _count_levels(lines: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for line in lines:
        level = _detect_level(line) or "unknown"
        counts[level] = counts.get(level, 0) + 1
    return counts


def _top_patterns(lines: List[str], n: int = 5) -> List[str]:
    """Return the n most common non-trivial words/tokens in log lines."""
    freq: Dict[str, int] = {}
    token_re = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")
    skip = {"INFO", "WARN", "WARNING", "ERROR", "DEBUG", "CRITICAL", "None"}
    for line in lines:
        for token in token_re.findall(line):
            if token.upper() not in skip and not token.upper() == token:
                freq[token] = freq.get(token, 0) + 1
    sorted_tokens = sorted(freq, key=lambda t: freq[t], reverse=True)
    return sorted_tokens[:n]


def summarize_logs(log_map: Dict[str, List[str]]) -> SnapSummary:
    """Build a SnapSummary from a mapping of service name -> log lines."""
    summaries = []
    for service, lines in log_map.items():
        svc_summary = ServiceSummary(
            service=service,
            total_lines=len(lines),
            level_counts=_count_levels(lines),
            top_patterns=_top_patterns(lines),
        )
        summaries.append(svc_summary)
    return SnapSummary(services=summaries)


def format_snap_summary(snap: SnapSummary) -> str:
    """Render a human-readable summary string."""
    lines = [f"Snapshot summary: {snap.service_count} service(s), {snap.total_lines} total lines"]
    for svc in snap.services:
        level_str = ", ".join(f"{k}={v}" for k, v in sorted(svc.level_counts.items()))
        patterns_str = ", ".join(svc.top_patterns) if svc.top_patterns else "—"
        lines.append(f"  [{svc.service}] {svc.total_lines} lines | {level_str or 'no levels'} | top: {patterns_str}")
    return "\n".join(lines)
