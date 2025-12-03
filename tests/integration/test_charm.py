import logging
from pathlib import Path

import jubilant

logger = logging.getLogger(__name__)


def test_deploy(charm: Path, juju: jubilant.Juju, config_file: str):
    """Deploy the charm under test."""
    config = {"config-file": config_file}
    juju.deploy(charm.resolve(), config=config, app="conserver")
    juju.wait(jubilant.all_active, timeout=300)
