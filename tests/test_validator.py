"""Tests for logsnap.validator."""

import pytest

from logsnap.config import ServiceConfig, SnapConfig
from logsnap.validator import ValidationResult, validate_config


def _make_svc(**kwargs) -> ServiceConfig:
    defaults = {"name": "web", "unit": "nginx.service", "lines": 100}
    defaults.update(kwargs)
    return ServiceConfig(**defaults)


def _make_config(*services, **kwargs) -> SnapConfig:
    return SnapConfig(services=list(services), **kwargs)


# --- ValidationResult helpers ---

def test_validation_result_ok_when_no_errors():
    vr = ValidationResult(warnings=["something minor"])
    assert vr.ok is True


def test_validation_result_not_ok_with_errors():
    vr = ValidationResult(errors=["bad thing"])
    assert vr.ok is False


def test_validation_result_str_valid():
    assert str(ValidationResult()) == "Config is valid."


def test_validation_result_str_shows_errors_and_warnings():
    vr = ValidationResult(errors=["oops"], warnings=["heads up"])
    text = str(vr)
    assert "[ERROR] oops" in text
    assert "[WARN]  heads up" in text


# --- validate_config ---

def test_valid_config_passes():
    cfg = _make_config(_make_svc())
    result = validate_config(cfg)
    assert result.ok
    assert result.errors == []


def test_no_services_is_error():
    cfg = _make_config()
    result = validate_config(cfg)
    assert not result.ok
    assert any("No services" in e for e in result.errors)


def test_service_with_no_unit_or_command_is_error():
    svc = ServiceConfig(name="db", unit=None, command=None)
    cfg = _make_config(svc)
    result = validate_config(cfg)
    assert not result.ok
    assert any("unit" in e and "command" in e for e in result.errors)


def test_service_with_empty_name_is_error():
    svc = ServiceConfig(name="  ", unit="foo.service")
    cfg = _make_config(svc)
    result = validate_config(cfg)
    assert not result.ok
    assert any("empty" in e for e in result.errors)


def test_duplicate_service_names_is_error():
    svc1 = _make_svc(name="api")
    svc2 = _make_svc(name="api")
    cfg = _make_config(svc1, svc2)
    result = validate_config(cfg)
    assert not result.ok
    assert any("Duplicate" in e for e in result.errors)


def test_both_unit_and_command_is_warning():
    svc = ServiceConfig(name="svc", unit="foo.service", command="journalctl -u foo")
    cfg = _make_config(svc)
    result = validate_config(cfg)
    assert result.ok  # warning, not error
    assert any("precedence" in w for w in result.warnings)


def test_nonpositive_lines_is_error():
    svc = ServiceConfig(name="svc", unit="foo.service", lines=0)
    cfg = _make_config(svc)
    result = validate_config(cfg)
    assert not result.ok
    assert any("lines" in e for e in result.errors)
