import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ['AUTH_TOKEN'] = 'testing'

from app.main import app


@pytest.fixture(name='client')
def client_fixture() -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient for testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(name='auth_headers')
def auth_headers_fixture() -> dict:
    """Return valid authorization headers for testing."""
    return {'Authorization': 'Token testing'}
