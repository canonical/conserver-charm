#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import base64
import binascii
import logging
import os
import pwd
from pathlib import Path
from typing import Optional, cast

import ops
from charmlibs import apt
from charms.operator_libs_linux.v1 import systemd

logger = logging.getLogger(__name__)

SERVER_CONFIG = "/etc/conserver/server.conf"
CONSERVER_CONFIG = "/etc/conserver/conserver.cf"
CONSERVER_PASSWD = "/etc/conserver/conserver.passwd"


class ConserverCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.conserver_deb = apt.DebianPackage.from_system("conserver-server")
        self.ipmitool_deb = apt.DebianPackage.from_system("ipmitool")
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)

    @property
    def conserver_cf(self) -> Optional[str]:
        """Return the conserver configuration from Juju config options, if any."""
        if contents := cast(str, self.config.get("config-file")):
            try:
                return base64.b64decode(contents).decode("utf-8")
            except binascii.Error as e:
                logger.exception("Failed to decode config-file content: %s", e)
                return None
        return None

    @property
    def conserver_passwd(self) -> Optional[str]:
        """Return the conserver password file from Juju config options, if any."""
        if contents := cast(str, self.config.get("passwd-file")):
            try:
                return base64.b64decode(contents).decode("utf-8")
            except binascii.Error as e:
                logger.exception("Failed to decode passwd-file content: %s", e)
                return None
        return None

    def _on_install(self, _):
        """Handle install event."""
        self.unit.status = ops.MaintenanceStatus("Installing conserver-server")
        self.conserver_deb.ensure(apt.PackageState.Latest)
        self.ipmitool_deb.ensure(apt.PackageState.Latest)

        # Keep default port for incoming connections at 3109
        # and set base port for established connections at 33000
        server_config = "OPTS='-p 3109 -b 33000  '\nASROOT=\n"
        try:
            Path(SERVER_CONFIG).write_text(server_config, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.exception("Failed to write server.conf: %s", e)
            self.unit.status = ops.BlockedStatus("Failed to write server.conf")

    def _on_config_changed(self, _):
        """Handle changes in configuration."""
        self.unit.status = ops.MaintenanceStatus("Updating configuration")

        conserver_cf = self.conserver_cf
        if conserver_cf:
            self._write_file(conserver_cf, Path(CONSERVER_CONFIG))

        conserver_passwd = self.conserver_passwd
        if conserver_passwd:
            self._write_file(
                conserver_passwd,
                Path(CONSERVER_PASSWD),
                uid=pwd.getpwnam("conservr").pw_uid,
                mode=0o600,
            )

        # Restart service to apply changes
        try:
            systemd.service_reload("conserver-server", restart_on_failure=True)
            logger.info("Reloaded Conserver service successfully")
        except systemd.SystemdError as e:
            logger.exception("Failed to reload Conserver service: %s", e)
        self.set_status()

    def _write_file(
        self, contents: str, path: Path, uid: int = 0, gid: int = 0, mode: int = 0o644
    ):
        """Write contents to a file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
            logger.info("Wrote %s successfully", path.name)
        except OSError as e:
            logger.exception("Failed to write %s: %s", path.name, e)
            return False
        os.chown(path, uid, gid)
        path.chmod(mode)
        return True

    def _on_start(self, _):
        """Handle start event."""
        try:
            systemd.service_enable("--now", "conserver-server")
            logger.info("Enabled and started Conserver service successfully")
        except systemd.SystemdError as e:
            logger.exception("Failed to enable/start Conserver service: %s", e)
        self.set_status()

    def set_status(self):
        """Calculate and set the unit status."""
        config_file = self.config.get("config-file", "")
        passwd_file = self.config.get("passwd-file", "")

        if not config_file:
            self.unit.status = ops.BlockedStatus("Missing config-file in config")
            return
        if config_file and self.conserver_cf is None:
            self.unit.status = ops.BlockedStatus("Invalid value for config-file")
            return

        if not passwd_file:
            self.unit.status = ops.BlockedStatus("Missing passwd-file in config")
            return
        if passwd_file and self.conserver_passwd is None:
            self.unit.status = ops.BlockedStatus("Invalid value for passwd-file")
            return

        if systemd.service_running("conserver-server"):
            self.unit.status = ops.ActiveStatus()
        elif systemd.service_failed("conserver-server"):
            self.unit.status = ops.BlockedStatus("Conserver service has failed")
        else:
            self.unit.status = ops.MaintenanceStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
