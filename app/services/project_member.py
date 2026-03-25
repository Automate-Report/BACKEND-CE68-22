from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.schemas.userauthen import UserInfo
from app.schemas.invite import InvitationResponse


import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_members import ProjectMember, InviteStatus, ProjectRole
from app.models.projects import Project
from app.models.users import User

class ProjectMemberService:

    async def get_user_roles_map(self, user_id: str, db: AsyncSession):
        """คืนค่า {project_id: role} สำหรับโปรเจกต์ที่ user เป็นสมาชิก"""
        query = sa.select(
            ProjectMember.project_id, 
            ProjectMember.role
        ).where(
            ProjectMember.user_email == user_id,
            ProjectMember.status == InviteStatus.JOINED
        )
        
        result = await db.execute(query)
        # สร้าง Dict Comprehension จากผลลัพธ์ (คอลัมน์ 0 คือ id, 1 คือ role)
        # .value เพื่อดึง String ออกมาจาก Enum
        return {row[0]: row[1].value for row in result.all()}
    
    async def get_user_info_by_project_id(self, project_id: int, db: AsyncSession):
        """ดึงข้อมูลสมาชิกทุกคนในโปรเจกต์ (Join ข้อมูล User มาให้ครบ)"""
        query = (
            sa.select(
                User.email,
                User.first_name,
                User.last_name,
                ProjectMember.role,
                ProjectMember.joined_at
            )
            .join(ProjectMember, User.email == ProjectMember.user_email)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.status == InviteStatus.JOINED
            )
        )

        result = await db.execute(query)
        rows = result.all()

        all_matches = []
        for email, f_name, l_name, role, joined_at in rows:
            user_info = UserInfo(
                email=email,
                firstname=f_name,
                lastname=l_name,
                role=role.value,  # ดึงค่าจาก Enum
                joinned_at=joined_at # ระวังชื่อตัวแปรใน Schema (joinned_at)
            )
            all_matches.append(user_info)

        return all_matches
    
    async def get_invitations_by_user_id(self, user_id: str, db: AsyncSession):
        """
        ดึงรายการคำเชิญทั้งหมดของผู้ใช้ พร้อมข้อมูลชื่อโปรเจกต์และชื่อเจ้าของ
        """
        # 1. สร้าง Query ที่ Join 3 ตารางเข้าด้วยกัน
        query = (
            sa.select(
                ProjectMember,             # ข้อมูล Invitation
                Project.name,               # ชื่อโปรเจกต์
                User.first_name,            # ชื่อเจ้าของ (Firstname)
                User.last_name              # นามสกุลเจ้าของ (Lastname)
            )
            .join(Project, ProjectMember.project_id == Project.id)
            .join(User, Project.user_email == User.email) # Join หาเจ้าของโปรเจกต์
            .where(ProjectMember.user_email == user_id)        # กรองเฉพาะของ User คนนี้
            .where(ProjectMember.status == InviteStatus.INVITED) # กรองเฉพาะที่ยังไม่ตอบรับ (Optional)
            .order_by(ProjectMember.invited_at.desc())
        )

        # 2. Execute
        result = await db.execute(query)
        rows = result.all()

        # 3. แปลงผลลัพธ์เป็น InvitationResponse
        return_result = []
        for member, p_name, f_name, l_name in rows:
            invite_response = InvitationResponse(
                project_id   = member.project_id,
                email        = member.user_email,
                project_name = p_name,
                project_owner= f"{f_name} {l_name}",
                role         = member.role,
                status       = member.status,
                invited_at   = member.invited_at
            )
            return_result.append(invite_response)

        return return_result
    
    async def invite_member(self, db: AsyncSession, user_id: str, role: str, project_id: int):
        # 1. ตรวจสอบก่อนว่าเคยถูกเชิญหรือเป็นสมาชิกแล้วหรือยัง (Query ครั้งเดียว)
        query = sa.select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_email == user_id
        )
        result = await db.execute(query)
        existing_member = result.scalar_one_or_none()

        if existing_member:
            if existing_member.status == InviteStatus.INVITED:
                # ✅ ใช้ HTTPException แทนการ return string
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="User is already invited to this project"
                )
            elif existing_member.status == InviteStatus.JOINED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="User is already a member of this project"
                )

        # 2. เตรียมข้อมูลสำหรับการ Insert
        # แปลง String Role ที่รับมาให้เป็น Enum (Pentester / Developer)
        try:
            role_enum = ProjectRole(role.lower())
        except ValueError:
            # ถ้าส่ง Role มาไม่ตรงกับ Enum ที่ตั้งไว้
            role_enum = ProjectRole.DEVELOPER

        new_member = ProjectMember(
            project_id=project_id,
            user_email=user_id,
            role=role_enum,
            status=InviteStatus.INVITED,
            invited_at=datetime.now(timezone.utc)
        )

        try:
            # 3. บันทึกลง Database
            db.add(new_member)
            await db.commit()
            await db.refresh(new_member)

            new_relation = {
                "project_id": new_member.project_id,
                "email": new_member.user_email,
                "role": new_member.role.value,
                "status": new_member.status.value,
                "invited_at": new_member.invited_at,
                "joinned_at": None
            }
            
            return new_relation
        except Exception as e:
            await db.rollback()
            print(f"❌ Error inviting member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    async def accept_invitation(self, user_id: str, project_id: int, db: AsyncSession):
        """
        ตอบรับคำเชิญเข้าโปรเจกต์ (SQL Version)
        """
        # 1. ค้นหาคำเชิญที่ตรงกับ user และ project โดยต้องมีสถานะเป็น 'invited' เท่านั้น
        query = sa.select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_email == user_id,
            ProjectMember.status == InviteStatus.INVITED
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            # หากไม่พบคำเชิญ หรืออาจจะตอบรับไปแล้ว
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already processed"
            )

        # 2. อัปเดตสถานะเป็น JOINED
        # การแก้ค่าผ่าน Object แบบนี้จะไปกระตุ้น @sa.event.listens_for ที่คุณเขียนไว้
        # ทำให้ joined_at ถูกเซตเป็น sa.sql.func.now() อัตโนมัติ
        member.status = InviteStatus.JOINED

        try:
            # 3. บันทึกการเปลี่ยนแปลง
            await db.commit()
            await db.refresh(member)

            # 4. ส่งกลับข้อมูลในรูปแบบ Dictionary (เลียนแบบ JSON เดิมแต่เป็น SQL Data)
            return {
                "project_id": member.project_id,
                "user_email": member.user_email,
                "role": member.role.value,
                "status": member.status.value,
                "invited_at": member.invited_at,
                "joinned_at": member.joined_at # ใน Model ชื่อ joined_at (n ตัวเดียว)
            }
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error accepting invitation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not accept invitation"
            )
    
    async def decline_invitation(self, user_id: str, project_id: int, db: AsyncSession):
        # 1. สร้างคำสั่งค้นหาเพื่อตรวจสอบก่อนลบ (หรือจะลบตรงๆ เลยก็ได้)
        # เงื่อนไข: ต้องเป็น user คนนี้, project นี้ และสถานะยังเป็น 'invited' เท่านั้น
        query = sa.delete(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_email == user_id,
            ProjectMember.status == InviteStatus.INVITED
        )

        try:
            # 2. Execute คำสั่ง Delete
            result = await db.execute(query)
            
            # 3. ตรวจสอบว่ามีแถวที่ถูกลบไปจริงไหม (rowcount)
            if result.rowcount == 0:
                # ถ้า rowcount เป็น 0 แสดงว่าไม่พบคำเชิญ หรือสถานะเปลี่ยนเป็น joined ไปก่อนแล้ว
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found or already accepted"
                )

            # 4. Commit การลบข้อมูล
            await db.commit()
            return True

        except HTTPException:
            # ปล่อย HTTPException ออกไปหา FastAPI
            raise
        except Exception as e:
            # หากเกิด Database Error อื่นๆ ให้ Rollback
            await db.rollback()
            print(f"❌ Error rejecting invitation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not process rejection"
            )
    
    async def get_role(self, user_id: str, project_id: int, db: AsyncSession):
        query = sa.select(ProjectMember).where(
            sa.and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_email == user_id
            )
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            return None
        
        return member.role

    
    async def change_role(self, user_id: str, role: str, project_id: int, db: AsyncSession):
        """อัปเดต Role ของสมาชิก และคืนค่า UserInfo ชุดใหม่"""
    
        # 1. ตรวจสอบ Role ใหม่ว่าถูกต้องตาม Enum หรือไม่
        try:
            new_role_enum = ProjectRole(role.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

        # 2. ค้นหาสมาชิกที่ต้องการอัปเดต (Join กับ User ไปเลยเพื่อเอาข้อมูลกลับมาทีเดียว)
        query = (
            sa.select(ProjectMember, User)
            .join(User, ProjectMember.user_email == User.email)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_email == user_id
            )
        )
        
        result = await db.execute(query)
        row = result.fetchone()

        if not row:
            return None

        member, user = row

        # 3. อัปเดต Role
        member.role = new_role_enum

        try:
            # 4. Commit การเปลี่ยนแปลง
            await db.commit()
            await db.refresh(member)

            # 5. ประกอบข้อมูลส่งกลับเป็น UserInfo
            return UserInfo(
                email=user.email,
                firstname=user.first_name, # ตรวจสอบชื่อฟิลด์ใน Model User
                lastname=user.last_name,
                role=member.role.value,
                joinned_at=member.joined_at # ระวังชื่อสะกด joinned_at ตาม Schema เดิมคุณ
            )
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating member role: {e}")
            raise HTTPException(status_code=500, detail="Could not update member role")
    
    async def delete_member(self, user_id: str, project_id: int, db: AsyncSession):
        """ลบสมาชิกออกจากโปรเจกต์ (SQL Version)"""
        
        # 1. สร้างคำสั่ง Delete โดยระบุเงื่อนไขให้ชัดเจน
        # ลบแถวที่มี project_id และ user_email ตรงตามที่ระบุ
        query = sa.delete(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_email == user_id
        )

        try:
            # 2. Execute คำสั่งลบ
            result = await db.execute(query)
            
            # 3. ตรวจสอบว่ามีการลบข้อมูลจริงไหม (rowcount)
            if result.rowcount == 0:
                # ถ้า rowcount เป็น 0 แสดงว่าไม่พบสมาชิกคนนี้ในโปรเจกต์ดังกล่าว
                return False

            # 4. Commit การลบข้อมูลลง Database
            await db.commit()
            return True

        except Exception as e:
            # หากเกิด Database Error ให้ Rollback ป้องกันข้อมูลค้างคิว
            await db.rollback()
            print(f"❌ Error removing member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not remove member from project"
            )

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_member_service = ProjectMemberService()