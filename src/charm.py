#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import base64
import binascii
import logging
import os
import pwd
import subprocess
from pathlib import Path

import ops
from charmlibs import apt

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

        # Update conserver.cf
        try:
            config_content = str(self.config["config-file"])
        except KeyError:
            logger.error("config-file not found in charm configuration")
            self.unit.status = ops.BlockedStatus("Missing config-file in config")
            return
        try:
            decoded_config = base64.b64decode(config_content).decode("utf-8")
        except binascii.Error as e:
            logging.exception("Failed to decode config-file content: %s", e)
            self.unit.status = ops.BlockedStatus("Invalid base64 in config-file")
            return
        try:
            Path(CONSERVER_CONFIG).write_text(decoded_config, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.exception("Failed to write conserver.cf: %s", e)
            self.unit.status = ops.BlockedStatus("Failed to write conserver.cf")
            return

        # Update conserver.passwd
        try:
            passwd_content = str(self.config["passwd-file"])
        except KeyError:
            logger.error("passwd-file not found in charm configuration")
            self.unit.status = ops.BlockedStatus("Missing passwd-file in config")
            return
        try:
            decoded_passwd = base64.b64decode(passwd_content).decode("utf-8")
        except binascii.Error as e:
            logger.exception("Failed to decode passwd-file content: %s", e)
            self.unit.status = ops.BlockedStatus("Invalid base64 in passwd-file")
            return
        try:
            Path(CONSERVER_PASSWD).write_text(decoded_passwd, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.exception("Failed to write conserver.passwd: %s", e)
            self.unit.status = ops.BlockedStatus("Failed to write conserver.passwd")
            return

        # conserver.cf should be owned by root:root
        os.chown(CONSERVER_CONFIG, 0, 0)
        os.chmod(CONSERVER_CONFIG, 0o644)

        # conserver.passwd should be owned by conservr:root
        conservr_uid = pwd.getpwnam("conservr").pw_uid
        os.chown(CONSERVER_PASSWD, conservr_uid, 0)
        os.chmod(CONSERVER_PASSWD, 0o600)

        # Restart service to apply changes
        try:
            subprocess.check_call(["systemctl", "restart", "conserver-server"])
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to restart Conserver service: %s", e)
            self.unit.status = ops.BlockedStatus("Service failed to restart")
        else:
            self.unit.status = ops.ActiveStatus()

    def _on_start(self, _):
        """Handle start event."""
        try:
            # Ensure service is running
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", "conserver-server"]
            )
            self.unit.status = ops.ActiveStatus()
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to start Conserver service: %s", e)
            self.unit.status = ops.BlockedStatus("Service failed to start")


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
