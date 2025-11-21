import logging
from unittest.mock import MagicMock

import pytest
from ops import testing

from charm import ConserverCharm

logger = logging.getLogger(__name__)


def test_start(monkeypatch: pytest.MonkeyPatch, config_file: str):
    """Test that the charm has the correct state after handling the start event."""
    ctx = testing.Context(ConserverCharm)

    systemd_mock = MagicMock()
    systemd_mock.service_running.return_value = True
    monkeypatch.setattr("charm.systemd", systemd_mock)

    state_in = testing.State(
        config={"config-file": config_file},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.ActiveStatus)


def test_start_missing_config_file(monkeypatch: pytest.MonkeyPatch):
    """Test that the charm is blocked when config-file is missing."""
    ctx = testing.Context(ConserverCharm)

    systemd_mock = MagicMock()
    monkeypatch.setattr("charm.systemd", systemd_mock)

    state_in = testing.State(
        config={},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


def test_start_failed_service(monkeypatch: pytest.MonkeyPatch, config_file: str):
    """Test that the charm is blocked when the service has failed."""
    ctx = testing.Context(ConserverCharm)

    systemd_mock = MagicMock()
    systemd_mock.service_running.return_value = False
    systemd_mock.service_failed.return_value = True
    monkeypatch.setattr("charm.systemd", systemd_mock)

    state_in = testing.State(
        config={"config-file": config_file},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)
