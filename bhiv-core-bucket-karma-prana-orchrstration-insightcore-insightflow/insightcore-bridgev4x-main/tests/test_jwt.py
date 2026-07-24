import time
from app.jwt_validators import validate_jwt


def test_valid_jwt():
    token = {"exp": time.time() + 60}
    assert validate_jwt(token) is True


def test_expired_jwt():
    token = {"exp": time.time() - 10}
    assert validate_jwt(token) is False
