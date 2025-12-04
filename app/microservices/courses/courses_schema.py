# app/microservices/courses/courses_schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

# ----------------- CATEGORY -----------------
class CategoryBase(BaseModel):
    category_name: str = Field(..., max_length=150)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, max_length=150)

class CategoryResponse(CategoryBase):
    category_id: int
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: bool

    class Config:
        orm_mode = True
        # for pydantic v2 compatibility you may use `from_attributes = True` in v2


# ----------------- SUBCATEGORY -----------------
class SubCategoryBase(BaseModel):
    sub_category_name: str = Field(..., max_length=150)
    category_id: int

class SubCategoryCreate(BaseModel):
    category_id: int
    sub_category_name: str


class SubCategoryUpdate(BaseModel):
    sub_category_name: Optional[str] = None  

class SubCategoryResponse(SubCategoryBase):
    sub_category_id: int
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: bool

    class Config:
        orm_mode = True


# ----------------- COURSE -----------------
class CourseBase(BaseModel):
    course_name: str = Field(..., max_length=300)
    course_link: HttpUrl
    course_subcategory: int

class CourseCreate(BaseModel):
    course_name: str
    course_link: str
    course_subcategory: int    # keep only this field


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_link: Optional[str] = None
    sub_category_id: Optional[int] = None

class CourseResponse(CourseBase):
    course_id: int
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: bool

    class Config:
        orm_mode = True
