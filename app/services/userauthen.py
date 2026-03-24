from fastapi import HTTPException
from datetime import datetime, timezone
from jose import jwt, JWTError

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User 

from app.schemas.userauthen import LoginRequest, UserCreate

from app.core.redis import redis_client
from app.core.jwt import create_access_token
from app.core.config import settings

class UserAuthenService:
    
    def blacklist_token(self, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as errormsg:
            print(errormsg)
            return  # Invalid token, cannot blacklist

        exp = payload["exp"]
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now

        if ttl <= 0:
            return  # token already expired
        
        print("token blacklisted :", token)

        redis_client.setex(token, ttl, "blacklisted")

    async def authenticate_user(self, loginRequest: LoginRequest, db: AsyncSession):
        """Service: ตรวจสอบการเข้าสู่ระบบของผู้ใช้"""
        query = sa.select(User).where(User.email == loginRequest.email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        print(user)
        if user and user.password == loginRequest.password:
            return create_access_token(loginRequest.email, user.first_name, user.last_name)
        # Check all but user not found
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    async def authenticate_user_google(self, userdata: dict, db: AsyncSession):
        query = sa.select(User)
        result = await db.execute(query)
        users = result.scalars().all()

        google_id = userdata["sub"]
        email = userdata["email"]
        firstname = userdata["given_name"]
        lastname = userdata["family_name"]
        picture = userdata["picture"]

        # check if alr had an account with this google_id
        for user in users:

            # has account
            if user.google_id == google_id:
                return create_access_token(email, firstname, lastname)

            # has account but without google oauth
            if user.email == email:
                user.google_id = google_id
                user.picture_path = picture
                user.updated_at = datetime.now().isoformat()

                try:
                    await db.commit()
                    await db.refresh(user) # Refresh to get any DB-generated fields
                except Exception as e:
                    await db.rollback()
                    raise e
                
                return create_access_token(email, firstname, lastname)                
        
        # create new user + login, if google_id not found in DB
        new_user = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "password": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "session_token": None,
            "google_id": google_id,
            "picture": picture
        }

        try:
            db.add(new_user)
            await db.commit()
            # refresh to get the DB generated content such as created_at
            await db.refresh(new_user)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create project")

        return create_access_token(email, firstname, lastname)
    
    async def create_user(self, createUser: UserCreate, db: AsyncSession):
        """Service: สร้างผู้ใช้ใหม่"""
        query = sa.select(User).where(User.email == createUser.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            new_user = User(
                first_name = createUser.firstName,
                last_name = createUser.lastName,
                email = createUser.email,
                password = createUser.password,
                google_id = None,
                picture_path = None,
            )
        
        try:
            db.add(new_user)
            await db.commit()
            # refresh to get the DB generated content such as created_at
            await db.refresh(new_user)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create user")
        # Only return non-sensitive info
        return {
            "email": createUser.email,
            "firstname": createUser.firstName,
            "lastname": createUser.lastName
        }
    
    async def get_user_by_id(self, user_id: str, db: AsyncSession):
        "Get User by ID"
        query = sa.select(User).where(User.email == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return user
    
    async def get_username_by_id(self, user_id: str, db: AsyncSession):
        query = sa.select(User).where(User.email == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None
        
        return f'{user.first_name} {user.last_name}'

# สร้าง instance ของ Service เพื่อใช้งาน
userauthen_service = UserAuthenService()