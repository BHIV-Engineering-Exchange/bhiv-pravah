import jwt
import time

SECRET_KEY = "demo-secret"
ALGORITHM = "HS256"

payload = {
    "sub": "demo-user",
    "iat": int(time.time()),
    "exp": int(time.time()) + 300   # 5 minutes
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
