"""Unit tests for config.py."""

import base64

from config import ConserverConfig


def test_config(config_file: str, passwd_file: str):
    """Test that config is parsed correctly."""
    config = ConserverConfig(config_file=config_file, passwd_file=passwd_file)
    assert config.config_file == base64.b64decode(config_file).decode()
    assert config.passwd_file == base64.b64decode(passwd_file).decode()
