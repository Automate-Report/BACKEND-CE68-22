from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.schemas.user import InfoPayload, PasswordPayload 

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
        
    async def get_profile(self, email:str, db: AsyncSession):
        query = sa.select(User).where(User.email == email)
        
        try:
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            return {
                "firstname" : user.first_name,
                "lastname" : user.last_name,
                "email" : user.email,
                "picture" : user.picture_path,
                "bio" : user.bio
            }

        except Exception as e:
            print(f"❌ Error checking user existence: {e}")
            return False
    
    async def edit_password(self, passwordform: PasswordPayload, user_email:str, db: AsyncSession):
        try:
            # 1. Find user by email
            query = sa.select(User).where(User.email == user_email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # 2. Check if old password matches
            if user.password != passwordform.old_password:
                return "Incorrect"

            # 3. Replace with new password
            user.password = passwordform.new_password

            await db.commit()
            return "Password updated successfully"

        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating password: {e}")
            return "Failed to update password"

    async def edit_info(self, infoForm: InfoPayload, user_email:str, db: AsyncSession):
        try:
            # 1. Find user by email
            query = sa.select(User).where(User.email == user_email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # 2. Replace info
            user.first_name = infoForm.firstname
            user.last_name = infoForm.lastname
            user.bio = infoForm.bio

            await db.commit()
            return "Password updated successfully"

        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating User info: {e}")
            return "Failed to update User info"

# สร้าง Instance ไว้ให้ Router เรียกใช้
user_service = UserService()