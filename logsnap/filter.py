"""Log filtering utilities for logsnap."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FilterConfig:
    """Criteria used to filter log lines."""

    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    min_level: Optional[str] = None

    # Ordered severity levels (lowest to highest)
    LEVELS = ["debug", "info", "warning", "error", "critical"]

    def _level_index(self, level: str) -> int:
        return self.LEVELS.index(level.lower()) if level.lower() in self.LEVELS else -1

    def matches(self, line: str) -> bool:
        """Return True if *line* passes all active filter criteria."""
        if self.min_level:
            min_idx = self._level_index(self.min_level)
            line_level = _detect_level(line)
            if line_level is not None and self._level_index(line_level) < min_idx:
                return False

        for pat in self.exclude_patterns:
            if re.search(pat, line):
                return False

        if self.include_patterns:
            return any(re.search(pat, line) for pat in self.include_patterns)

        return True


def _detect_level(line: str) -> Optional[str]:
    """Best-effort extraction of a log level keyword from *line*."""
    for level in FilterConfig.LEVELS:
        if re.search(rf"\b{level}\b", line, re.IGNORECASE):
            return level
    return None


def apply_filter(lines: List[str], cfg: FilterConfig) -> List[str]:
    """Return only the lines from *lines* that satisfy *cfg*."""
    return [line for line in lines if cfg.matches(line)]
