#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import base64
import binascii
import logging
from typing import Optional, cast

import ops

from conserver import Conserver

logger = logging.getLogger(__name__)


class ConserverCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.conserver = Conserver()
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

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
        self.conserver.install()

    def _on_config_changed(self, _):
        """Handle changes in configuration."""
        self.unit.status = ops.MaintenanceStatus("Updating configuration")

        conserver_cf = self.conserver_cf
        if conserver_cf:
            self.conserver.write_conserver_config(conserver_cf)

        conserver_passwd = self.conserver_passwd
        if conserver_passwd:
            self.conserver.write_passwd_file(conserver_passwd)

        # Restart service to apply changes
        self.conserver.reload(restart_on_failure=True, ignore_errors=True)
        self.set_status()

    def _on_start(self, _):
        """Handle start event."""
        self.conserver.start(ignore_errors=True)
        self.unit.set_workload_version(self.conserver.version)
        self.set_status()

    def _on_stop(self, _):
        """Handle stop event."""
        self.conserver.stop(ignore_errors=True)
        self.conserver.uninstall()

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

        if self.conserver.running:
            self.unit.status = ops.ActiveStatus()
        elif self.conserver.failed:
            self.unit.status = ops.BlockedStatus("Conserver service has failed")
        else:
            self.unit.status = ops.MaintenanceStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
