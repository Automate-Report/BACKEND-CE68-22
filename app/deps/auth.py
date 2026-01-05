# deps/auth.py
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from app.core.redis import redis_client
from app.core.config import authen_settings

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # check if token is blacklisted
    if redis_client.exists(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked"
        )

    try:
        payload = jwt.decode(
            token,
            authen_settings.SECRET_KEY,
            algorithms=[authen_settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return payload
