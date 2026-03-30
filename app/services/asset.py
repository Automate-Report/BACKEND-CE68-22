import math

from fastapi import HTTPException

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assets import Asset, AssetType

from app.schemas.asset import AssetCreate


class AssetService:

    async def get_all_assets(self, project_id: int, page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        query = (
            sa.select(Asset)
            .where(Asset.project_id == project_id)
        )

        if search:
            query = query.where(Asset.name.ilike(f"%{search}%"))

        if filter and filter != "ALL":
            if filter == "ip":
                query = query.where(Asset.type == AssetType.IP)
            elif filter == "url":
                query = query.where(Asset.type == AssetType.URL)

        if sort_by:
            column = getattr(Asset, sort_by, Asset.created_at)
            if order == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        # 4. Sorting
        column = getattr(Asset, sort_by if sort_by else "created_at", Asset.created_at)
        query = query.order_by(column.desc() if order == "desc" else column.asc())

        # 5. SQL-Level Pagination (LIMIT & OFFSET)
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 6. Execute Final Query
        result = await db.execute(query)
        rows = result.scalars().all()

        paginated_items = []
        for asset in rows:
            paginated_items.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "project_id": asset.project_id,
                    "description": asset.description,
                    "target": asset.target,
                    "type": asset.type,
                    "updated_at": asset.updated_at
                }
            )

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": math.ceil(total_count / size),
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    async def get_asset_by_id(self, asset_id:int, db: AsyncSession) -> Asset:
        query = (
            sa.select(Asset)
            .where(Asset.id == asset_id)
        )
        result = await db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        return asset
    
    async def get_all_asset_names_for_dropdown(self, project_id: int, db: AsyncSession) :
        """Service: ดึงชื่อ Asset ทั้งหมดในโปรเจกต์ สำหรับ Dropdown"""
        query = (
            sa.select(Asset)
            .where(Asset.project_id == project_id)
        )
        result = await db.execute(query)
        assets = result.scalars().all()

        filtered_assets = []
        for asset in assets:
            filtered_assets.append({
                "name": asset.name,
                "id": asset.id,
                "target": asset.target
            })
        return filtered_assets

    async def create_asset(self, asset_in: AssetCreate, db: AsyncSession) -> dict:
        """Service: สร้าง Asset ใหม่"""
        new_asset_db = Asset(
            name = asset_in.name,
            project_id = asset_in.project_id,
            description = asset_in.description,
            target = asset_in.target,
            type = asset_in.type,
        )

        try:
            db.add(new_asset_db)
            await db.commit()

            await db.refresh(new_asset_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create asset")
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_asset = {
            "id": new_asset_db.id,
            "name": new_asset_db.name,
            "project_id": new_asset_db.project_id,
            "description": new_asset_db.description,
            "target": new_asset_db.target,
            "type": new_asset_db.type,
            "created_at": new_asset_db.created_at,
            "updated_at": new_asset_db.updated_at,
        }
        
        return new_asset
    
    async def update_asset(self, asset_id: int, asset_in: AssetCreate, db: AsyncSession):
        """Service: อัปเดต Asset"""
        query = sa.select(Asset).where(Asset.id == asset_id)
        result = await db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return None
        
        
    
        asset.name = asset_in.name
        asset.description = asset_in.description
        asset.target = asset_in.target

        if asset_in.type == "IP":
            asset.type = AssetType.IP
        elif asset_in.type == "URL":
            asset.type = AssetType.URL

        try:
            await db.commit()
            await db.refresh(asset)

            return {
                "id": asset.id,
                "name": asset.name,
                "project_id": asset.project_id,
                "description": asset.description,
                "target": asset.target,
                "type": asset.type,
                "updated_at": asset.updated_at
            }
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def delete_asset(self, asset_id: int, db: AsyncSession):
        """Service: ลบ Asset"""
        query = (
            sa.select(Asset)
            .where(Asset.id == asset_id)
        )
        result = await db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return False
        
        try:
            # 2. Delete using the session
            await db.delete(asset)
            
            # 3. Commit the transaction
            await db.commit()
            return True
        except Exception as e:
            # 4. Rollback if something goes wrong (e.g., Foreign Key constraint)
            await db.rollback()
            print(f"Delete Error: {e}")
            return False
    
    async def get_asset_ids_by_project_id(self, project_id: int, db: AsyncSession):
        query = (
            sa.select(Asset.id)
            .where(Asset.project_id == project_id)
        )
        result = await db.execute(query)
        assets = result.scalars().all()

        return assets
    
    async def get_assets_by_project_id(self, project_id: int, db: AsyncSession):
        query = (
            sa.select(Asset)
            .where(Asset.project_id == project_id)
        )
        result = await db.execute(query)
        assets = result.scalars().all()

        return assets
    
    async def cnt_asset_by_project_id(self, project_id: int, db: AsyncSession):
        query = (
            sa.select(Asset)
            .where(Asset.project_id == project_id)
        )
        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        return total_count


# สร้าง Instance ไว้ให้ Router เรียกใช้
asset_service = AssetService()