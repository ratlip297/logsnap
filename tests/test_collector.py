"""Tests for logsnap.collector."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from logsnap.collector import collect_service_logs, collect_all
from logsnap.config import ServiceConfig, SnapConfig


@pytest.fixture()
def simple_service() -> ServiceConfig:
    return ServiceConfig(name="myapp", command="echo 'hello log'")


@pytest.fixture()
def snap_config(simple_service: ServiceConfig) -> SnapConfig:
    return SnapConfig(services=[simple_service], default_lines=100)


def _mock_run(stdout: str = "", returncode: int = 0):
    result = MagicMock()
    result.stdout = stdout
    result.stderr = ""
    result.returncode = returncode
    return result


def test_collect_service_logs_uses_custom_command(simple_service):
    fake_output = "2024-01-01 INFO starting up\n"
    with patch("logsnap.collector.subprocess.run", return_value=_mock_run(fake_output)) as mock_run:
        output = collect_service_logs(simple_service)

    assert output == fake_output
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd == simple_service.command


def test_collect_service_logs_raises_on_nonzero_exit(simple_service):
    with patch(
        "logsnap.collector.subprocess.run",
        return_value=_mock_run(returncode=1),
    ):
        with pytest.raises(RuntimeError, match="Log collection failed"):
            collect_service_logs(simple_service)


def test_collect_service_logs_no_command_no_journalctl():
    service = ServiceConfig(name="ghost", command=None)
    with patch("logsnap.collector.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="journalctl not found"):
            collect_service_logs(service)


def test_collect_all_writes_files(tmp_path: Path, snap_config: SnapConfig):
    fake_logs = "line1\nline2\n"
    with patch(
        "logsnap.collector.collect_service_logs", return_value=fake_logs
    ):
        written = collect_all(snap_config, output_dir=tmp_path)

    assert "myapp" in written
    log_file = written["myapp"]
    assert log_file.exists()
    assert log_file.read_text() == fake_logs


def test_collect_all_skips_failed_services(tmp_path: Path):
    services = [
        ServiceConfig(name="good", command="echo ok"),
        ServiceConfig(name="bad", command="false"),
    ]
    config = SnapConfig(services=services, default_lines=50)

    def fake_collect(service, **kwargs):
        if service.name == "bad":
            raise RuntimeError("boom")
        return "some logs\n"

    with patch("logsnap.collector.collect_service_logs", side_effect=fake_collect):
        written = collect_all(config, output_dir=tmp_path)

    assert "good" in written
    assert "bad" not in written
