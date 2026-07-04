import os

# Use isolated test database — never touch the dev/production SQLite file
os.environ["DATABASE_URL"] = "sqlite:///./test_finance_tracker.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    if os.path.exists("test_finance_tracker.db"):
        os.remove("test_finance_tracker.db")
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_finance_tracker.db"):
        os.remove("test_finance_tracker.db")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
