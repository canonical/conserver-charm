#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import base64
import logging
import os
import pwd
import subprocess
from pathlib import Path

import ops
from charms.operator_libs_linux.v0 import apt

logger = logging.getLogger(__name__)

CONSERVER_CONFIG = "/etc/conserver/conserver.cf"
CONSERVER_PASSWD = "/etc/conserver/conserver.passwd"


class ConserverCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)

    def _on_install(self, _):
        """Handle install event."""
        self.unit.status = ops.MaintenanceStatus("Installing conserver-server")
        self.install_apt_packages(["conserver-server", "ipmitool"])

        # Keep default port for incoming connections at 3109
        # and set base port for established connections at 33000
        server_config = "OPTS='-p 3109 -b 33000  '\nASROOT=\n"
        try:
            Path("/etc/conserver/server.conf").write_text(server_config)
        except Exception as e:
            logger.error("Failed to write server.conf: %s", str(e))
            self.unit.status = ops.BlockedStatus("Failed to write server.conf")
            return

    def install_apt_packages(self, packages: list):
        """Perform 'apt-get install -y."""
        try:
            apt.update()
            apt.add_package(packages)
        except apt.PackageError:
            logger.error("could not install package")
            self.unit.status = ops.BlockedStatus("Failed to install packages")

    def _on_config_changed(self, _):
        """Handle changes in configuration."""
        self.unit.status = ops.MaintenanceStatus("Updating configuration")

        try:
            # Update conserver.cf
            config_content = self.config["config-file"]
            try:
                decoded_config = base64.b64decode(config_content).decode(
                    "utf-8"
                )
            except Exception as e:
                logger.error(f"Failed to decode config-file content: {e}")
                self.unit.status = ops.BlockedStatus(
                    "Invalid base64 in config-file"
                )
                return
            Path(CONSERVER_CONFIG).write_text(decoded_config)

            # Update conserver.passwd
            passwd_content = self.config["passwd-file"]
            try:
                decoded_passwd = base64.b64decode(passwd_content).decode(
                    "utf-8"
                )
            except Exception as e:
                logger.error(f"Failed to decode passwd-file content: {e}")
                self.unit.status = ops.BlockedStatus(
                    "Invalid base64 in passwd-file"
                )
                return

            Path(CONSERVER_PASSWD).write_text(decoded_passwd)

            # conserver.cf should be owned by root:root
            os.chown(CONSERVER_CONFIG, 0, 0)
            os.chmod(CONSERVER_CONFIG, 0o644)

            # conserver.passwd should be owned by conservr:root
            conservr_uid = pwd.getpwnam("conservr").pw_uid
            os.chown(CONSERVER_PASSWD, conservr_uid, 0)
            os.chmod(CONSERVER_PASSWD, 0o600)

            # Restart service to apply changes
            subprocess.check_call(["systemctl", "restart", "conserver-server"])

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            self.unit.status = ops.BlockedStatus(
                f"Failed to update configuration: {str(e)}"
            )
            return

        self.unit.status = ops.ActiveStatus()

    def _on_start(self, _):
        """Handle start event."""
        try:
            # Ensure service is running
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", "conserver-server"]
            )
            self.unit.status = ops.ActiveStatus()
        except subprocess.CalledProcessError:
            self.unit.status = ops.BlockedStatus("Service failed to start")


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
