import logging
from unittest.mock import MagicMock, patch

from ops import testing

from charm import ConserverCharm

logger = logging.getLogger(__name__)


@patch("charm.Conserver")
def test_invalid_base64_config_file(conserver_mock: MagicMock):
    """Test that the charm is blocked when config-file has invalid base64 content."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": "invalid-base64"},
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


@patch("charm.Conserver")
def test_invalid_base64_passwd_file(conserver_mock: MagicMock, config_file: str):
    """Test that the charm is blocked when passwd-file has invalid base64 content."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={
            "config-file": config_file,
            "passwd-file": "invalid-base64",
        },
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


@patch("charm.Conserver")
def test_install(conserver_mock: MagicMock):
    """Test that the charm installs conserver on install event."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(leader=True)
    ctx.run(ctx.on.install(), state_in)
    conserver_mock.return_value.install.assert_called_once()


@patch("charm.Conserver")
def test_config_missing_config_file(conserver_mock: MagicMock):
    """Test that the charm is blocked when config-file is missing."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": ""},
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


@patch("charm.Conserver")
def test_config_missing_passwd_file(conserver_mock: MagicMock, config_file: str):
    """Test that the charm is blocked when passwd-file is missing."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": config_file, "passwd-file": ""},
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


@patch("charm.Conserver")
def test_start(conserver_mock: MagicMock, config_file: str):
    """Test that the charm has the correct state after handling the start event."""
    conserver_mock.return_value.running = True
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": config_file},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.ActiveStatus)


@patch("charm.Conserver")
def test_start_failed_service(conserver_mock: MagicMock, config_file: str):
    """Test that the charm is blocked when the service has failed."""
    conserver_mock.return_value.running = False
    conserver_mock.return_value.failed = True
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": config_file},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.BlockedStatus)


@patch("charm.Conserver")
def test_start_maintenance(conserver_mock: MagicMock, config_file: str):
    """Test that the charm is in maintenance when the service is not running nor failed."""
    conserver_mock.return_value.running = False
    conserver_mock.return_value.failed = False
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(
        config={"config-file": config_file},
        leader=True,
    )
    state_out = ctx.run(ctx.on.start(), state_in)
    assert isinstance(state_out.unit_status, testing.MaintenanceStatus)


@patch("charm.Conserver")
def test_stop(conserver_mock: MagicMock):
    """Test that the charm stops and uninstalls conserver on stop event."""
    ctx = testing.Context(ConserverCharm)
    state_in = testing.State(leader=True)
    ctx.run(ctx.on.stop(), state_in)
    conserver_mock.return_value.stop.assert_called_once()
    conserver_mock.return_value.uninstall.assert_called_once()
