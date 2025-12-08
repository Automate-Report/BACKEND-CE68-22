from typing import Generic, TypeVar, List
from pydantic import BaseModel
from pydantic.generics import GenericModel

# กำหนด Type Variable
T = TypeVar("T")

# Schema สำหรับการตอบกลับแบบ Pagination
class PaginatedResponse(GenericModel, Generic[T]):
    total: int       # จำนวนข้อมูลทั้งหมด (ใน DB)
    page: int        # หน้าปัจจุบัน
    size: int        # จำนวนต่อหน้า
    total_pages: int # จำนวนหน้าทั้งหมด
    items: List[T]   # ข้อมูลจริง (ProjectResponse)