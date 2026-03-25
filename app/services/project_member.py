import json
import os
from typing import List
from datetime import datetime

from app.schemas.userauthen import UserInfo
from app.schemas.invite import InvitationResponse
from app.services.userauthen import userauthen_service

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_members import ProjectMember, InviteStatus
from app.models.projects import Project
from app.models.users import User



# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "project_members.json")

class ProjectMemberService:
    
    def _ensure_dummy_folder_exists(self):
        """ตรวจสอบว่ามี folder dummy_data หรือยัง ถ้าไม่มีให้สร้าง"""
        folder = os.path.dirname(JSON_FILE_PATH)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _read_json(self) -> List[dict]:
        """อ่านข้อมูลจากไฟล์ JSON"""
        if not os.path.exists(JSON_FILE_PATH):
            return []
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # ถ้าไฟล์เสียหรือว่างเปล่า ให้คืนค่า list ว่าง

    def _save_json(self, data: List[dict]):
        """บันทึกข้อมูลลงไฟล์ JSON"""
        self._ensure_dummy_folder_exists()
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            # default=str ช่วยแปลง datetime เป็น string อัตโนมัติ
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def get_user_roles_map(self, user_id: str):
        """คืนค่า {project_id: role} สำหรับโปรเจกต์ที่ user เป็นสมาชิก"""
        relations = self._read_json() # อ่านไฟล์ relation json
        return {rel["project_id"]: rel["role"] for rel in relations if rel["email"] == user_id and rel["status"] == "joined"}
    
    def get_user_info_by_project_id(self, project_id: int):
        relations = self._read_json()

        all_matches = []
        for rel in relations:
            if rel["project_id"] == project_id and rel["status"] == "joined":
                
                user = userauthen_service.get_user_by_id(rel["email"])

                user_info = UserInfo(
                    email=user["email"],
                    firstname=user["firstname"],
                    lastname=user["lastname"],
                    role=rel["role"],
                    joinned_at=rel["joinned_at"]
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
                email        = member.email,
                project_name = p_name,
                project_owner= f"{f_name} {l_name}",
                role         = member.role,
                status       = member.status,
                invited_at   = member.invited_at
            )
            return_result.append(invite_response)

        return return_result
    
    def invite_member(self, user_id: str, role: str, project_id: int):
        relations = self._read_json()

        # เช็คก่อนว่า user นี้เคยถูก invite หรือเป็นสมาชิกโปรเจกต์นี้แล้วหรือยัง
        for rel in relations:
            if rel["project_id"] == project_id and rel["email"] == user_id:
                if rel["status"] == "invited":
                    return "already invited" 
                else:
                    return "already a member"

        new_relation = {
            "project_id": project_id,
            "email": user_id,
            "role": role,
            "status": "invited",
            "invited_at": datetime.now().isoformat(),
            "joinned_at": None
        }
        relations.append(new_relation)
        self._save_json(relations)
        return new_relation
    
    def accept_invitation(self, user_id: str, project_id: int):
        relations = self._read_json()

        for rel in relations:
            if rel["project_id"] == project_id and rel["email"] == user_id and rel["status"] == "invited":
                rel["status"] = "joined"
                rel["joinned_at"] = datetime.now().isoformat()
                self._save_json(relations)
                return rel
            
        return None
    
    def decline_invitation(self, user_id: str, project_id: int):
        relations = self._read_json()

        for i, rel in enumerate(relations):
            if rel["project_id"] == project_id and rel["email"] == user_id and rel["status"] == "invited":
                del relations[i]
                self._save_json(relations)
                return True
            
        return False
    
    def get_role(self, user_id: str, project_id: int):

        relations = self._read_json()

        for rel in relations:
            if rel["project_id"] == project_id and rel["email"] == user_id:
                return rel["role"]
            
        return None
    
    def change_role(self, user_id: str, role: str, project_id: int):
        relations = self._read_json()
        new_user_info = None
        for rel in relations:
            if rel["project_id"] == project_id and rel["email"] == user_id:
                rel["role"] = role
                
                user = userauthen_service.get_user_by_id(rel["email"])

                user_info = UserInfo(
                    email=user["email"],
                    firstname=user["firstname"],
                    lastname=user["lastname"],
                    role=role,
                    joinned_at=rel["joinned_at"]
                )

                new_user_info = user_info

        if new_user_info:
            self._save_json(relations)
            return new_user_info
            
        return None
    
    def delete_member(self, user_id: str, project_id: int):

        relations = self._read_json()

        for i, rel in enumerate(relations):
            if rel["project_id"] == project_id and rel["email"] == user_id:
                del relations[i]
                self._save_json(relations)
                return True
            
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_member_service = ProjectMemberService()