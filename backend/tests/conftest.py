import os

os.environ.setdefault("LLM_MOCK", "1")

import pytest


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from src.api.app import app

    with TestClient(app) as test_client:
        yield test_client
