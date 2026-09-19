import pytest
from fastapi.testclient import TestClient
from app.chain import Assistant
from app.main import create_app

@pytest.fixture
def assistant():
    return Assistant("demo")

@pytest.fixture
def client(assistant):
    with TestClient(create_app(assistant)) as test_client:
        yield test_client
