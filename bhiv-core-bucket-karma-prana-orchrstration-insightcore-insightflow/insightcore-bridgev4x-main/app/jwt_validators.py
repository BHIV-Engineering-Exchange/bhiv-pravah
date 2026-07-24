import jwt
import time

SECRET_KEY = "demo-secret"
ALGORITHM = "HS256"

def validate_jwt(token: str) -> bool:
    try:
        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        exp = decoded.get("exp")
        if exp is None:
            return False

        if exp <= time.time():
            return False

        return True

    except jwt.PyJWTError:
        return False
