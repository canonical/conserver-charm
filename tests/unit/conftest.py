import pytest
from ops import testing

from charm import ConserverCharm


@pytest.fixture(scope="function")
def ctx() -> testing.Context:
    """Return the Conserver Charm context."""
    return testing.Context(ConserverCharm)
