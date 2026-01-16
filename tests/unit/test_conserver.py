"""Unit tests for conserver workload."""

from unittest.mock import MagicMock, patch

import pytest
from charmlibs import apt, systemd

from conserver import CONSERVER_SERVICE, Conserver


@patch("conserver.subprocess.run")
@patch("conserver.apt.DebianPackage.from_system")
def test_version(from_system_mock: MagicMock, subprocess_run_mock: MagicMock):
    """Test that version property returns correct value."""
    subprocess_run_mock.return_value = MagicMock(
        stdout=b"conserver: conserver.com version 8.2.6\n", returncode=0
    )
    conserver = Conserver()
    assert conserver.version == "8.2.6"


@patch("conserver.subprocess.run")
@patch("conserver.apt.DebianPackage.from_system")
def test_version_unknown(from_system_mock: MagicMock, subprocess_run_mock: MagicMock):
    """Test that version property returns 'unknown' when version cannot be determined."""
    subprocess_run_mock.return_value = MagicMock(stdout=b"unexpected output", returncode=0)
    conserver = Conserver()
    assert conserver.version == "unknown"


@patch("conserver.pwd.getpwnam")
def test_uid(getpwnam_mock: MagicMock):
    """Test that uid property returns correct value."""
    mock_pwd_entry = MagicMock()
    mock_pwd_entry.pw_uid = 1001
    getpwnam_mock.return_value = mock_pwd_entry

    conserver = Conserver()
    assert conserver.uid == 1001


@patch("conserver.systemd.service_running", return_value=True)
def test_running(running_mock: MagicMock):
    """Test that running property returns correct value."""
    conserver = Conserver()
    assert conserver.running is True
    running_mock.assert_called_once_with(CONSERVER_SERVICE)


@patch("conserver.systemd.service_failed", return_value=True)
def test_failed(failed_mock: MagicMock):
    """Test that failed property returns correct value."""
    conserver = Conserver()
    assert conserver.failed is True
    failed_mock.assert_called_once_with(CONSERVER_SERVICE)


@patch("conserver.Conserver.write_server_config")
@patch("conserver.apt.DebianPackage.from_system")
def test_install(from_system_mock: MagicMock, write_config_mock: MagicMock):
    """Test that conserver is installed and server config is written."""
    conserver = Conserver()
    conserver.install()
    conserver.conserver_deb.ensure.assert_called_with(apt.PackageState.Latest)  # type: ignore
    write_config_mock.assert_called_once()


@patch("conserver.apt.DebianPackage.from_system")
def test_uninstall(from_system_mock: MagicMock):
    """Test that conserver is uninstalled."""
    conserver = Conserver()
    conserver.uninstall()
    conserver.conserver_deb.ensure.assert_called_with(apt.PackageState.Absent)  # type: ignore


@patch("conserver.systemd.service_enable")
def test_start(service_enable_mock: MagicMock):
    """Test that start method enables and starts the service."""
    conserver = Conserver()
    conserver.start()
    service_enable_mock.assert_called_once_with("--now", CONSERVER_SERVICE)


@patch("conserver.systemd.service_enable", side_effect=systemd.SystemdError)
def test_start_ignore_errors(service_enable_mock: MagicMock):
    """Test that start method ignores errors when specified."""
    conserver = Conserver()
    conserver.start(ignore_errors=True)


@patch("conserver.systemd.service_enable", side_effect=systemd.SystemdError)
def test_start_raise_errors(service_enable_mock: MagicMock):
    """Test that start method raises errors when not ignoring."""
    conserver = Conserver()
    pytest.raises(systemd.SystemdError, conserver.start, ignore_errors=False)


@patch("conserver.systemd.service_reload")
def test_reload(service_reload_mock: MagicMock):
    """Test that reload method reloads the service."""
    conserver = Conserver()
    conserver.reload(restart_on_failure=True)
    service_reload_mock.assert_called_once_with(CONSERVER_SERVICE, restart_on_failure=True)


@patch("conserver.systemd.service_reload", side_effect=systemd.SystemdError)
def test_reload_ignore_errors(service_reload_mock: MagicMock):
    """Test that reload method ignores errors when specified."""
    conserver = Conserver()
    conserver.reload(ignore_errors=True)


@patch("conserver.systemd.service_reload", side_effect=systemd.SystemdError)
def test_reload_raise_errors(service_reload_mock: MagicMock):
    """Test that reload method raises errors when not ignoring."""
    conserver = Conserver()
    pytest.raises(systemd.SystemdError, conserver.reload, ignore_errors=False)


@patch("conserver.systemd.service_disable")
def test_stop(service_disable_mock: MagicMock):
    """Test that stop method disables the service."""
    conserver = Conserver()
    conserver.stop()
    service_disable_mock.assert_called_once_with("--now", CONSERVER_SERVICE)


@patch("conserver.systemd.service_disable", side_effect=systemd.SystemdError)
def test_stop_ignore_errors(service_disable_mock: MagicMock):
    """Test that stop method ignores errors when specified."""
    conserver = Conserver()
    conserver.stop(ignore_errors=True)


@patch("conserver.systemd.service_disable", side_effect=systemd.SystemdError)
def test_stop_raise_errors(service_disable_mock: MagicMock):
    """Test that stop method raises errors when not ignoring."""
    conserver = Conserver()
    pytest.raises(systemd.SystemdError, conserver.stop, ignore_errors=False)


@patch("conserver.Path.write_text")
def test_write_server_config(write_text_mock: MagicMock):
    """Test that server config is written to the correct file."""
    conserver = Conserver()
    conserver.write_server_config()
    write_text_mock.assert_called_once()


@patch("conserver.Path.write_text", side_effect=OSError)
def test_write_server_config_failure(write_text_mock: MagicMock):
    """Test that write_server_config raises an error on failure."""
    conserver = Conserver()
    pytest.raises(OSError, conserver.write_server_config)


@patch("conserver.Path")
@patch("conserver.os.chown")
def test_write_conserver_config(chown_mock: MagicMock, path_mock: MagicMock):
    """Test that conserver config is written correctly."""
    conserver = Conserver()
    test_content = "test conserver config"
    conserver.write_conserver_config(test_content)
    path_mock.return_value.write_text.assert_called_once_with(test_content, encoding="utf-8")
    path_mock.return_value.chmod.assert_called_once()
    chown_mock.assert_called_once()


@patch("conserver.Path.write_text", side_effect=OSError)
def test_write_conserver_config_failure(write_text_mock: MagicMock):
    """Test that write_conserver_config raises an error on failure."""
    conserver = Conserver()
    pytest.raises(OSError, conserver.write_conserver_config, "test content")


@patch("conserver.Conserver.uid", new_callable=MagicMock(return_value=1))
@patch("conserver.Path")
@patch("conserver.os.chown")
def test_write_passwd_file(chown_mock: MagicMock, path_mock: MagicMock, uid_mock: MagicMock):
    """Test that passwd file is written correctly."""
    conserver = Conserver()
    test_content = "test passwd content"
    conserver.write_passwd_file(test_content)
    path_mock.return_value.write_text.assert_called_once_with(test_content, encoding="utf-8")
    path_mock.return_value.chmod.assert_called_once()
    chown_mock.assert_called_once()


@patch("conserver.Path.write_text", side_effect=OSError)
def test_write_passwd_file_failure(write_text_mock: MagicMock):
    """Test that write_passwd_file raises an error on failure."""
    conserver = Conserver()
    pytest.raises(OSError, conserver.write_passwd_file, "test content")
