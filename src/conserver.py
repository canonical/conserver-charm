"""Functions for managing and interacting with conserver."""

import logging
import os
import pwd
import re
import subprocess
from pathlib import Path

from charmlibs import apt, systemd

logger = logging.getLogger(__name__)

CONSERVER_DEB = "conserver-server"
IPMITOOL_DEB = "ipmitool"
CONSERVER_SERVICE = "conserver-server"
CONSERVER_USER = "conservr"

SERVER_CONF = "/etc/conserver/server.conf"
CONSERVER_CF = "/etc/conserver/conserver.cf"
CONSERVER_PASSWD = "/etc/conserver/conserver.passwd"

# Keep default port for incoming connections at 3109
# and set base port for established connections at 33000
SERVER_CONFIG = "OPTS='-p 3109 -b 33000  '\nASROOT=\n"


class Conserver:
    """Represents the conserver application/workload."""

    def __init__(self):
        self.conserver_deb = apt.DebianPackage.from_system(CONSERVER_DEB)
        self.ipmitool_deb = apt.DebianPackage.from_system(IPMITOOL_DEB)

    @property
    def version(self) -> str:
        """Get the installed version of conserver."""
        stdout = subprocess.check_output(["conserver", "-V"], text=True).strip()
        match = re.search(r"conserver.com version (\S+)", stdout)
        if match:
            return match.group(1)
        return "unknown"

    @property
    def uid(self) -> int:
        """Get the conserver user identifier."""
        return pwd.getpwnam(CONSERVER_USER).pw_uid

    @property
    def running(self) -> bool:
        """Check if the conserver service is running."""
        return systemd.service_running(CONSERVER_SERVICE)

    @property
    def failed(self) -> bool:
        """Check if the conserver service has failed."""
        return systemd.service_failed(CONSERVER_SERVICE)

    def install(self) -> None:
        """Install conserver."""
        self.conserver_deb.ensure(apt.PackageState.Latest)
        self.ipmitool_deb.ensure(apt.PackageState.Latest)
        self.write_server_config()

    def uninstall(self) -> None:
        """Uninstall conserver."""
        self.conserver_deb.ensure(apt.PackageState.Absent)
        self.ipmitool_deb.ensure(apt.PackageState.Absent)

    def start(self, ignore_errors: bool = False) -> None:
        """Start the conserver service."""
        try:
            systemd.service_enable("--now", CONSERVER_SERVICE)
            logger.info("Started %s service", CONSERVER_SERVICE)
        except systemd.SystemdError as e:
            logger.error("Failed to start %s service: %s", CONSERVER_SERVICE, e)
            if not ignore_errors:
                raise

    def reload(self, restart_on_failure: bool = False, ignore_errors: bool = False) -> None:
        """Reload the conserver service."""
        try:
            systemd.service_reload(CONSERVER_SERVICE, restart_on_failure=restart_on_failure)
            logger.info("Reloaded %s service", CONSERVER_SERVICE)
        except systemd.SystemdError as e:
            logger.error("Failed to reload %s service: %s", CONSERVER_SERVICE, e)
            if not ignore_errors:
                raise

    def stop(self, ignore_errors: bool = False) -> None:
        """Stop the conserver service."""
        try:
            systemd.service_disable("--now", CONSERVER_SERVICE)
            logger.info("Stopped %s service", CONSERVER_SERVICE)
        except systemd.SystemdError as e:
            logger.error("Failed to stop %s service: %s", CONSERVER_SERVICE, e)
            if not ignore_errors:
                raise

    def write_server_config(self) -> None:
        """Write the server.conf file."""
        try:
            Path(SERVER_CONF).write_text(SERVER_CONFIG, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.error("Failed to write %s: %s", SERVER_CONF, e)
            raise

    def write_conserver_config(self, contents: str) -> None:
        """Write the conserver.cf file."""
        path = Path(CONSERVER_CF)
        try:
            path.write_text(contents, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.error("Failed to write %s: %s", CONSERVER_CF, e)
            raise
        os.chown(path, 0, 0)
        path.chmod(0o644)

    def write_passwd_file(self, contents: str) -> None:
        """Write the conserver.passwd file."""
        path = Path(CONSERVER_PASSWD)
        try:
            path.write_text(contents, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logger.error("Failed to write %s: %s", CONSERVER_PASSWD, e)
            raise
        os.chown(path, self.uid, 0)
        path.chmod(0o600)
