# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""Charm configuration."""

from pydantic import Base64Str, BaseModel

PASSWD_FILE = """\
# Conserver passwd file
# Format: username:$1$Y0ZjMm2h$oMX5UyLi1/y0Q9IRWf3v/0
# you can generate the hashed password using `openssl passwd -1`
"""


class ConserverConfig(BaseModel):
    """Conserver Charm configuration."""

    config_file: Base64Str = ""
    passwd_file: Base64Str = PASSWD_FILE
