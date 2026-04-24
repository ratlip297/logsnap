"""Configuration loader for logsnap services."""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ServiceConfig:
    name: str
    log_path: str
    format: str = "json"  # json or plaintext
    enabled: bool = True
    filters: List[str] = field(default_factory=list)


@dataclass
class SnapConfig:
    output_dir: str = "./snapshots"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    services: List[ServiceConfig] = field(default_factory=list)
    max_lines: Optional[int] = None
    compress: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "SnapConfig":
        services = [
            ServiceConfig(**svc)
            for svc in data.get("services", [])
        ]
        return cls(
            output_dir=data.get("output_dir", "./snapshots"),
            timestamp_format=data.get("timestamp_format", "%Y%m%d_%H%M%S"),
            services=services,
            max_lines=data.get("max_lines"),
            compress=data.get("compress", True),
        )

    @classmethod
    def from_file(cls, path: str) -> "SnapConfig":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        return {
            "output_dir": self.output_dir,
            "timestamp_format": self.timestamp_format,
            "max_lines": self.max_lines,
            "compress": self.compress,
            "services": [
                {
                    "name": s.name,
                    "log_path": s.log_path,
                    "format": s.format,
                    "enabled": s.enabled,
                    "filters": s.filters,
                }
                for s in self.services
            ],
        }
