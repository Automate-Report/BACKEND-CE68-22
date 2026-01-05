import os
from app.core.config import authen_settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = authen_settings.DATABASE_URL

# 1. สร้าง Async Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# 2. สร้าง SessionMaker สำหรับสร้าง session ใหม่ในแต่ละ request
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 3. Base Class สำหรับ Model
class Base(DeclarativeBase):
    pass

# ฟังก์ชันสำหรับ Dependency Injection ใน API Routes
async def get_db():
    async with async_session() as session:
        yield session