import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User 

class UserService:

    async def is_user_exist(self, email:str, db: AsyncSession):
        """
        ตรวจสอบว่ามี User อีเมลนี้อยู่ในระบบหรือไม่ (SQL Version)
        """
        # 1. สร้าง Query เพื่อเช็คว่ามีแถวที่ email ตรงกันไหม
        # ใช้ sa.exists() จะมีประสิทธิภาพสูงที่สุด (สเกลได้ดีกว่าดึงข้อมูลมาทั้งก้อน)
        query = sa.select(sa.exists().where(User.email == email))
        
        try:
            # 2. Execute และดึงค่า Boolean ออกมา
            result = await db.execute(query)
            return result.scalar() # คืนค่า True ถ้าเจอ, False ถ้าไม่เจอ

        except Exception as e:
            print(f"❌ Error checking user existence: {e}")
            return False


# สร้าง Instance ไว้ให้ Router เรียกใช้
user_service = UserService()