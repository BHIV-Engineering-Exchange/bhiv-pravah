from .jwt_validators import validate_jwt
from .replay_guard import check_and_store
from .exceptions import EnforcementError

def enforce(token: dict, nonce: str) -> None:
    if not validate_jwt(token):
        raise EnforcementError("INVALID_OR_EXPIRED_JWT")

    if not check_and_store(nonce):
        raise EnforcementError("REPLAY_DETECTED")

    return None
