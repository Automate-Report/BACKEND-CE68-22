from app.core.config import settings
from jose import jwt
from datetime import datetime, timedelta, timezone

def create_access_token(email: str, firstname: str, lastname: str):
    # create JWT
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return {
        "token": token,
        "user": {
            "email": email,
            "firstname": firstname,
            "lastname": lastname
        }
    }