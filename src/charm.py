#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import base64
import binascii
import logging
import os
import pwd
import secrets
import string
from pathlib import Path
from typing import Optional, cast

import ops
from charmlibs import apt
from charms.operator_libs_linux.v1 import systemd
from passlib.hash import md5_crypt

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
        self.framework.observe(self.on.stop, self._on_stop)
        self.framework.observe(
            self.on.relation_changed, self._on_relation_event
        )
        self.framework.observe(
            self.on.relation_broken, self._on_relation_event
        )

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

        conserver_passwd = self._set_passwd_file()
        if conserver_passwd:
            self._write_file(
                conserver_passwd,
                Path(CONSERVER_PASSWD),
                uid=pwd.getpwnam("conservr").pw_uid,
                mode=0o600,
            )

        # Restart service to apply changes
        self._restart_conserver_service()

    def _on_start(self, _):
        """Handle start event."""
        try:
            systemd.service_enable("--now", "conserver-server")
            logger.info("Enabled and started Conserver service successfully")
        except systemd.SystemdError as e:
            logger.exception("Failed to enable/start Conserver service: %s", e)
        self.set_status()

    def _on_stop(self, _):
        """Handle stop event."""
        try:
            systemd.service_disable("--now", "conserver-server")
            logger.info("Disabled and stopped Conserver service successfully")
        except systemd.SystemdError as e:
            logger.exception("Failed to disable/stop Conserver service: %s", e)
        self.conserver_deb.ensure(apt.PackageState.Absent)
        self.ipmitool_deb.ensure(apt.PackageState.Absent)

    def _on_relation_event(self, event: ops.RelationEvent):
        """Handle relation event.

        :event: The relation event object.
        """
        if isinstance(event, ops.RelationBrokenEvent):
            logger.info(
                "Relation broken event detected for relation %s",
                event.relation.name,
            )
        if isinstance(event, ops.RelationChangedEvent):
            logger.info(
                "Relation changed event detected for relation %s",
                event.relation.name,
            )
        logger.info("Updating conserver.passwd due to relation event")
        # Update the conserver.passwd file to reflect relation changes
        self._on_config_changed(event)

    def set_status(self):
        """Calculate and set the unit status."""
        config_file = self.config.get("config-file", "")
        passwd_file = self.config.get("passwd-file", "")

        if not config_file:
            self.unit.status = ops.BlockedStatus(
                "Missing config-file in config"
            )
            return
        if config_file and self.conserver_cf is None:
            self.unit.status = ops.BlockedStatus(
                "Invalid value for config-file"
            )
            return

        if not passwd_file:
            self.unit.status = ops.BlockedStatus(
                "Missing passwd-file in config"
            )
            return
        if passwd_file and self.conserver_passwd is None:
            self.unit.status = ops.BlockedStatus(
                "Invalid value for passwd-file"
            )
            return

        if systemd.service_running("conserver-server"):
            self.unit.status = ops.ActiveStatus()
        elif systemd.service_failed("conserver-server"):
            self.unit.status = ops.BlockedStatus(
                "Conserver service has failed"
            )
        else:
            self.unit.status = ops.MaintenanceStatus()

    def _write_file(
        self,
        contents: str,
        path: Path,
        uid: int = 0,
        gid: int = 0,
        mode: int = 0o644,
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

    def _restart_conserver_service(self):
        """Restart the conserver service."""
        try:
            systemd.service_reload("conserver-server", restart_on_failure=True)
            logger.info("Reloaded Conserver service successfully")
        except systemd.SystemdError as e:
            logger.exception("Failed to reload Conserver service: %s", e)
        self.set_status()

    def _set_passwd_file(self):
        """Define conserver.passwd from all sources.

        This method ensures that the passwd file contains user entries
        provided via configuration as well as from related charms.
        """
        # Retrieve configuration set from config file
        passwd_config = self.conserver_passwd

        # Retrieve user entries from related charms
        relation_entries = []
        for relation in self.model.relations.get("conserver", []):
            if user_entry := self._get_user_entry_from_relation(relation):
                relation_entries.append(user_entry)

        # If neither source provides entries, log a warning and return None
        # This is required to set the status appropriately
        if not passwd_config and not relation_entries:
            logger.warning("No entries found for conserver.passwd")
            return None

        # Combine entries from config and relations
        if not passwd_config:
            conserver_passwd = "\n".join(relation_entries)
        else:
            conserver_passwd = (
                passwd_config + "\n" + "\n".join(relation_entries)
            )
        return conserver_passwd

    def _get_user_entry_from_relation(
        self, relation: ops.Relation
    ) -> Optional[str]:
        """Extract or generate a user entry for this relation.

        :relation: The relation object to extract user info from.
        :returns: A string in the format 'username:hashed_password'
        """
        # Define a unique username per relation
        username = f"{relation.app.name}-{relation.id}"
        relation.data[self.app]["username"] = username

        # Check if we already have credentials for this relation
        password = relation.data[self.app].get("password")

        if not password:
            # Generate new password and store in relation data
            password = self.generate_password()

            # Store in relation data for remote app access
            relation.data[self.app]["password"] = password

        hashed_password = self.hash_password(password)
        return f"{username}:{hashed_password}"

    def generate_password(self, length: int = 32) -> str:
        """Generate a randomized string to use as a password.

        :length: Length of the password to generate.
        :returns: A randomized string that can be used as a password.
        """
        return "".join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(length)
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using MD5 for conserver.passwd.

        :password: The plaintext password to hash.
        :returns: An MD5 hashed password string.
        """
        return md5_crypt.hash(password)


if __name__ == "__main__":  # pragma: nocover
    ops.main(ConserverCharm)  # type: ignore
