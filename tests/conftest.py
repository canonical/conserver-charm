import base64
import logging
import os
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config_file():
    """Return the config-file charm configuration value."""
    if "CONFIG_FILE" in os.environ:
        cf_path = Path(os.environ["CONFIG_FILE"])
        if not cf_path.exists():
            raise FileNotFoundError(f"config-file does not exist: {cf_path}")
        return base64.b64encode(cf_path.read_bytes()).decode("utf-8")
    cf_path = Path("tests/data/conserver.cf")
    if not cf_path.exists():
        raise FileNotFoundError(f"config-file does not exist: {cf_path}")
    return base64.b64encode(cf_path.read_bytes()).decode("utf-8")


@pytest.fixture(scope="session")
def passwd_file():
    """Return the passwd-file charm configuration value."""
    if "PASSWD_FILE" in os.environ:
        pf_path = Path(os.environ["PASSWD_FILE"])
        if not pf_path.exists():
            raise FileNotFoundError(f"passwd-file does not exist: {pf_path}")
        return base64.b64encode(pf_path.read_bytes()).decode("utf-8")
    pf_path = Path("tests/data/conserver.passwd")
    if not pf_path.exists():
        raise FileNotFoundError(f"passwd-file does not exist: {pf_path}")
    return base64.b64encode(pf_path.read_bytes()).decode("utf-8")
