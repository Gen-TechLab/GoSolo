import os
import sys

import pytest

# make "import app" work when running pytest from the project folder
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module  # noqa: E402
import db  # noqa: E402


@pytest.fixture
def client(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")  # fresh database for every test
    db.init_db()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.fixture
def agent(client):
    client.post("/login", data={"login": "agent", "password": "agent123"})
    return client
