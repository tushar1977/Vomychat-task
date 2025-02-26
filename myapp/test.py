import pytest
import json
from myapp import create_app, db
from myapp.models import User, Referral, Reward
from dotenv import load_dotenv
import os

load_dotenv()

username = os.environ.get("DB_USERNAME")
password = os.environ.get("DB_PASSWORD")
hostname = os.environ.get("DB_HOSTNAME")
database = os.environ.get("DB_TEST_NAME")
port = os.environ.get("DB_PORT", 3306)

test_config = {
    "SQLALCHEMY_DATABASE_URI": f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "TESTING": True,
}


@pytest.fixture(scope="session")
def app():
    app = create_app(test_config)

    with app.app_context():
        db.create_all()
        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_ping(client):
    response = client.get("/api/")
    assert response.status_code == 200


def test_register(client):
    response = client.post(
        "/api/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )
    data = json.loads(response.data)

    assert response.status_code == 201
    assert "user_id" in data
    assert "referral_code" in data
    app = create_app(test_config)
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.username == "testuser"


def test_register_with_weak_password(client):
    response = client.post(
        "/api/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
        },
    )

    assert response.status_code == 400
    assert b"Password must be at least 8 characters" in response.data


def test_register_duplicate_email(client):
    client.post(
        "/api/register",
        json={
            "username": "testuser1",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/register",
        json={
            "username": "testuser2",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 400
    assert b"Email already in use" in response.data


def test_login(client):
    client.post(
        "/api/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/login", json={"identifier": "testuser", "password": "Password123!"}
    )

    assert response.status_code == 200
    assert b"Login successful" in response.data


def test_login_invalid_credentials(client):
    client.post(
        "/api/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/login", json={"identifier": "testuser", "password": "WrongPassword123!"}
    )

    assert response.status_code == 401
    assert b"Invalid credentials" in response.data


def test_referral_system(client):
    response1 = client.post(
        "/api/register",
        json={
            "username": "referrer",
            "email": "referrer@example.com",
            "password": "Password123!",
        },
    )
    data1 = json.loads(response1.data)
    referral_code = data1["referral_code"]

    response2 = client.post(
        "/api/register",
        json={
            "username": "referred",
            "email": "referred@example.com",
            "password": "Password123!",
            "referral_code": referral_code,
        },
    )

    assert response2.status_code == 201
    app = create_app(test_config)
    with app.app_context():
        referrer = User.query.filter_by(username="referrer").first()
        referred = User.query.filter_by(username="referred").first()

        assert referred.referred_by == referrer.id

        referral = Referral.query.filter_by(
            referrer_id=referrer.id, referred_user_id=referred.id
        ).first()
        assert referral is not None

        reward = Reward.query.filter_by(
            user_id=referrer.id, referral_id=referral.id
        ).first()
        assert reward is not None
        assert reward.reward_type == "credit"
        assert reward.amount == 10.0


def test_forgot_password_flow(client):
    client.post(
        "/api/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    response = client.post("/api/forgot-password", json={"email": "test@example.com"})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "reset_url" in data

    reset_token = data["reset_url"].split("=")[1]

    response = client.post(
        f"/api/reset-password?token={reset_token}",
        json={"new_password": "NewPassword456!"},
    )

    assert response.status_code == 200

    response = client.post(
        "/api/login",
        json={"identifier": "test@example.com", "password": "NewPassword456!"},
    )

    assert response.status_code == 200
    assert b"Login successful" in response.data
