import os
import sys

import pytest

# Add the repository root when pytest is launched as a console script.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src import app as app_module  # noqa: E402
from src import db  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("AERODATABOX_API_KEY", raising=False)
    db.DB_PATH = str(tmp_path / "test.db")  # fresh database for every test
    db.init_db()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.fixture
def agent(client):
    client.post("/login", data={"login": "agent", "password": "agent123"})
    return client
