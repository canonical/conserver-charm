import logging
from pathlib import Path

import jubilant

logger = logging.getLogger(__name__)

APP_NAME = "conserver"


def test_deploy(charm: Path, juju: jubilant.Juju, config_file: str):
    """Deploy the charm under test."""
    config = {"config-file": config_file}
    juju.deploy(charm.resolve(), config=config, app=APP_NAME)
    juju.wait(jubilant.all_active, timeout=300)


def test_workload_version_is_set(juju: jubilant.Juju):
    """Test that the workload version is set after deployment."""
    version = juju.status().apps[APP_NAME].version
    task = juju.exec("conserver -V", unit=f"{APP_NAME}/0")
    version_output = task.stdout.strip()
    assert f"conserver.com version {version}" in version_output
