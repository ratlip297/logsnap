"""Tests for logsnap config loading and initialization."""

import json
import os
import pytest
from logsnap.config import SnapConfig, ServiceConfig
from logsnap.config_init import write_default_config, load_or_init_config


@pytest.fixture
def tmp_config_path(tmp_path):
    return str(tmp_path / "logsnap.config.json")


def test_service_config_defaults():
    svc = ServiceConfig(name="myapp", log_path="/logs/myapp.log")
    assert svc.format == "json"
    assert svc.enabled is True
    assert svc.filters == []


def test_snap_config_from_dict():
    data = {
        "output_dir": "/tmp/snaps",
        "compress": False,
        "services": [
            {"name": "web", "log_path": "/var/log/web.log", "format": "plaintext",
             "enabled": True, "filters": ["ERROR"]}
        ],
    }
    config = SnapConfig.from_dict(data)
    assert config.output_dir == "/tmp/snaps"
    assert config.compress is False
    assert len(config.services) == 1
    assert config.services[0].name == "web"
    assert config.services[0].filters == ["ERROR"]


def test_snap_config_from_file(tmp_config_path):
    data = {
        "output_dir": "./out",
        "compress": True,
        "services": [{"name": "svc1", "log_path": "/logs/svc1.log",
                       "format": "json", "enabled": True, "filters": []}],
    }
    with open(tmp_config_path, "w") as f:
        json.dump(data, f)

    config = SnapConfig.from_file(tmp_config_path)
    assert config.output_dir == "./out"
    assert config.services[0].name == "svc1"


def test_from_file_missing_raises():
    with pytest.raises(FileNotFoundError):
        SnapConfig.from_file("/nonexistent/path/config.json")


def test_write_default_config(tmp_config_path):
    path = write_default_config(tmp_config_path)
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert "services" in data
    assert len(data["services"]) > 0


def test_write_default_config_no_overwrite(tmp_config_path):
    write_default_config(tmp_config_path)
    with pytest.raises(FileExistsError):
        write_default_config(tmp_config_path, overwrite=False)


def test_load_or_init_creates_config(tmp_config_path):
    config = load_or_init_config(tmp_config_path)
    assert isinstance(config, SnapConfig)
    assert os.path.exists(tmp_config_path)
