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
