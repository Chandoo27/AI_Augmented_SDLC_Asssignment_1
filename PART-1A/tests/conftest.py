from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    from src.main import create_app

    app = create_app(tmp_path / "tasks.json")
    with TestClient(app) as test_client:
        yield test_client
