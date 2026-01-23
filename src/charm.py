#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

from config import ConserverConfig
from conserver import Conserver

logger = logging.getLogger(__name__)


class ConserverCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.typed_config = self.load_config(ConserverConfig, errors="blocked")
        self.conserver = Conserver()
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

    def _on_install(self, _):
        """Handle install event."""
        self.unit.status = ops.MaintenanceStatus("Installing conserver-server")
        self.conserver.install()

    def _on_config_changed(self, _):
        """Handle changes in configuration."""
        self.unit.status = ops.MaintenanceStatus("Updating configuration")
        self.conserver.write_conserver_config(self.typed_config.config_file)
        self.conserver.write_passwd_file(self.typed_config.passwd_file)
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
        if not self.typed_config.config_file:
            self.unit.status = ops.BlockedStatus("Missing config-file in config")
            return
        if not self.typed_config.passwd_file:
            self.unit.status = ops.BlockedStatus("Missing passwd-file in config")
            return

        if self.conserver.running:
            self.unit.status = ops.ActiveStatus()
        elif self.conserver.failed:
            self.unit.status = ops.BlockedStatus("Conserver service has failed")
        else:
            self.unit.status = ops.MaintenanceStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
