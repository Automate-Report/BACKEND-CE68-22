import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase

from pathlib import Path
# หา path ของไฟล์ .env ที่อยู่ที่ root ของโปรเจกต์
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# load_dotenv('../.env') # โหลด .env จาก root folder โดยอัตโนมัติ

DATABASE_URL = os.getenv("DATABASE_URL")

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