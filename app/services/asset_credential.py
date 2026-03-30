from fastapi import HTTPException

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.asset_credentials import AssetCredential
from app.schemas.asset_credential import AssetCredentialCreate

class AssetCredentialService:

    async def get_credential_by_id(self, credential_id:int, db: AsyncSession):
        query = sa.select(AssetCredential).where(AssetCredential.id == credential_id)
        result = await db.execute(query)
        cred = result.scalar_one_or_none()

        if not cred:
            return None
            
        return cred
    
    async def get_credential_by_asset_id(self, asset_id: int, db: AsyncSession):
        query = (
            sa.select(AssetCredential)
            .where(AssetCredential.asset_id == asset_id)
            .order_by(AssetCredential.created_at.desc()) # ✅ เรียงจากใหม่ไปเก่า
            .limit(1) # ✅ เอามาแค่ใบเดียวพอ
        )
        result = await db.execute(query)
        
        # ✅ ใช้ .scalar() จะปลอดภัยกว่า .scalar_one_or_none() เมื่อเราคุมด้วย .limit(1) แล้ว
        return result.scalar()

    async def create_credential(self, credential_in: AssetCredentialCreate, db: AsyncSession) -> dict:
        """Service: สร้าง Credential ใหม่"""
        new_asset_credential_db = AssetCredential(
            asset_id = credential_in.asset_id,
            username = credential_in.username,
            password = credential_in.password,
        )

        try:
            db.add(new_asset_credential_db)
            await db.commit()
            await db.refresh(new_asset_credential_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create credential")
        
        new_credential = {
            "id": new_asset_credential_db.id,
            "asset_id": new_asset_credential_db.asset_id,
            "username": new_asset_credential_db.username,
            "password": new_asset_credential_db.password,
            "created_at": new_asset_credential_db.created_at,
            "updated_at": new_asset_credential_db.updated_at,
        }
        
        return new_credential
    
    async def update_credential(self, credential_id: int, credential_in: AssetCredentialCreate, db: AsyncSession):
        """Service: อัปเดต Credential"""
        query = sa.select(AssetCredential).where(AssetCredential.id == credential_id)
        reuslt = await db.execute(query)
        cred = reuslt.scalar_one_or_none()

        if not cred:
            return None
        
        cred.username = credential_in.username
        cred.password = credential_in.password

        try:
            await db.commit()
            await db.refresh(cred) # This ensures all DB-generated fields are loaded

            return True
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def delete_credential(self, credential_id: int, db: AsyncSession) -> bool:
        """Service: ลบ Credential"""
        query = sa.select(AssetCredential).where(AssetCredential.id == credential_id)
        reuslt = await db.execute(query)
        cred = reuslt.scalar_one_or_none()

        if not cred:
            return None
        
        try:
            # 2. Delete using the session
            await db.delete(cred)
            
            # 3. Commit the transaction
            await db.commit()
            return True
        except Exception as e:
            # 4. Rollback if something goes wrong (e.g., Foreign Key constraint)
            await db.rollback()
            print(f"Delete Error: {e}")
            return False


# สร้าง Instance ไว้ให้ Router เรียกใช้
asset_credential_service = AssetCredentialService()