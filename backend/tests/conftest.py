"""Shared pytest fixtures.

Each test runs against a fresh in-memory SQLite database, so tests are
isolated and need no PostgreSQL instance. ``get_db`` is overridden rather than
patched globally, which keeps the production wiring untouched.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

# Settings are read at import time, so the environment must be prepared before
# any application module is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-finance-module")
os.environ.setdefault("AUTH_REQUIRED", "true")
os.environ.setdefault("CURRENCY_CODE", "USD")
os.environ.setdefault("CURRENCY_SYMBOL", "$")
os.environ.setdefault("COMPANY_NAME", "Test Company Ltd")
os.environ.setdefault("COMPANY_EMAIL", "billing@testcompany.example")
os.environ.setdefault("COMPANY_ADDRESS", "1 Test Street, Test City")

from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import ALGORITHM  # noqa: E402
from app.database.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Customer  # noqa: E402  (registers every table on Base)


@pytest.fixture()
def db_session():
    """A SQLAlchemy session bound to a private in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """A TestClient whose requests share the test's database session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _token(user_id: int, role: str) -> str:
    """Mint an access token matching the Authentication module's contract."""
    from datetime import datetime, timezone

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture()
def user_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(1, 'user')}"}


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(2, 'admin')}"}


@pytest.fixture()
def customer(db_session) -> Customer:
    record = Customer(
        full_name="Ada Lovelace",
        company_name="Analytical Engines Ltd",
        email="ada@example.com",
        phone="+441234567890",
        address="12 Computing Way",
        city="London",
        country="United Kingdom",
        status="active",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture()
def quotation_payload(customer) -> dict:
    """A quotation with deliberately awkward numbers.

    3 x 19.99 = 59.97 and 2 x 0.10 = 0.20 — the 0.10 line is exactly the value
    that float arithmetic gets wrong, so these fixtures double as a regression
    guard on Decimal handling.
    """
    return {
        "customer_id": customer.id,
        "items": [
            {"description": "Consulting hours", "quantity": 3, "unit_price": 19.99},
            {"description": "Punch cards", "quantity": 2, "unit_price": 0.10},
        ],
        "discount_type": "percentage",
        "discount_value": 10,
        "tax_rate": 20,
    }


@pytest.fixture()
def created_invoice(client, user_headers, customer) -> dict:
    """A sent invoice totalling exactly 100.00, for payment tests."""
    response = client.post(
        "/api/v1/invoices",
        headers=user_headers,
        json={
            "customer_id": customer.id,
            "items": [{"description": "Flat fee", "quantity": 1, "unit_price": 100}],
            "discount_value": 0,
            "tax_rate": 0,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
