"""
Welele Media™ — Universal Pytest Configuration & Test Isolation Fixture
Enforces strict Architectural Boundary Isolation:
1. Primary Protection: pytest_configure hook automatically clones state into an ephemeral isolated universe
   before any collection, fixture, or test runs. Each test module starts from a pristine copy of the baseline.
2. Secondary Protection: Canonical Production Store read-only write guard (RuntimeError on unauthorized writes).
"""

import pytest
from database import db

def pytest_configure(config):
    """
    Hook called immediately when pytest initializes.
    Ensures test isolation is permanently active before any test or fixture runs.
    """
    db.enable_test_isolation()

def pytest_unconfigure(config):
    """
    Hook called when pytest shuts down.
    Tears down the isolated test universe.
    """
    db.disable_test_isolation()

@pytest.fixture(autouse=True, scope="module")
def isolate_module_universe():
    """
    Guarantees every test module begins from the pristine canonical baseline,
    while allowing tests within the module to share sequential workflow state.
    """
    db.reset_test_state()
    yield
    db.reset_test_state()
