"""Validate SnapConfig and ServiceConfig for common misconfigurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from logsnap.config import SnapConfig, ServiceConfig


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"[ERROR] {e}")
        for w in self.warnings:
            lines.append(f"[WARN]  {w}")
        return "\n".join(lines) if lines else "Config is valid."


def _validate_service(svc: ServiceConfig, result: ValidationResult) -> None:
    if not svc.name or not svc.name.strip():
        result.errors.append("A service has an empty or missing name.")
    if not svc.unit and not svc.command:
        result.errors.append(
            f"Service '{svc.name}': must specify either 'unit' or 'command'."
        )
    if svc.unit and svc.command:
        result.warnings.append(
            f"Service '{svc.name}': both 'unit' and 'command' set; 'command' takes precedence."
        )
    if svc.lines is not None and svc.lines <= 0:
        result.errors.append(
            f"Service '{svc.name}': 'lines' must be a positive integer, got {svc.lines}."
        )


def validate_config(config: SnapConfig) -> ValidationResult:
    result = ValidationResult()

    if not config.services:
        result.errors.append("No services defined in configuration.")
        return result

    names_seen: set[str] = set()
    for svc in config.services:
        _validate_service(svc, result)
        if svc.name in names_seen:
            result.errors.append(f"Duplicate service name: '{svc.name}'.")
        names_seen.add(svc.name)

    if config.output_dir and not config.output_dir.strip():
        result.errors.append("'output_dir' is set but empty.")

    return result
