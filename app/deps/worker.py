import jwt # Use PyJWT
from fastapi import HTTPException, Depends, Header
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.workers import Worker
from app.models.access_keys import AccessKey

async def get_current_worker(
    authorization: str = Header(None), 
    db: AsyncSession = Depends(get_db)
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    token = authorization.split(" ")[1]

    try:
        # Step 1: Peek inside to get the worker ID
        # PyJWT syntax for unverified decode
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        worker_id_str = unverified_payload.get("sub")
        if not worker_id_str:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        worker_id = int(worker_id_str)

        # Step 2: Fetch the SECRET (access_key) for THIS worker only
        query = (
            sa.select(Worker, AccessKey.key)
            .join(AccessKey, Worker.access_key_id == AccessKey.id)
            .where(Worker.id == worker_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=401, detail="Worker or Key not found")

        # row[0] is Worker object, row[1] is the string key
        real_secret = row[1] 

        # Step 3: Real verification using the worker's unique secret
        payload = jwt.decode(token, real_secret, algorithms=["HS256"])
        
        return int(payload.get("sub"))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.InvalidTokenError, Exception) as e:
        print(f"Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")