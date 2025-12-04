# app/microservices/courses/courses_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from datetime import datetime

from app.db.models.db_base import CourseCategory, CourseSubCategory, Courses

# ---------------- CATEGORY SERVICES ----------------
async def create_category_service(data, user_id: int, session: AsyncSession):
    new = CourseCategory(
        category_name=data.category_name,
        created_by=user_id,
        created_at=datetime.utcnow(),
        is_deleted=False,
    )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new


async def list_categories_service(session: AsyncSession) -> List[CourseCategory]:
    result = await session.execute(select(CourseCategory).where(CourseCategory.is_deleted == False))
    return result.scalars().all()


async def get_category_by_id_service(category_id: int, session: AsyncSession) -> CourseCategory:
    result = await session.execute(
        select(CourseCategory).where(
            CourseCategory.category_id == category_id,
            CourseCategory.is_deleted == False
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


async def update_category_service(category_id: int, data, session: AsyncSession, user_id: int):
    cat = await get_category_by_id_service(category_id, session)

    values = {}
    if getattr(data, "category_name", None) is not None:
        values["category_name"] = data.category_name

    if not values:
        return cat

    values.update({"updated_by": user_id, "updated_at": datetime.utcnow()})
    stmt = update(CourseCategory).where(CourseCategory.category_id == category_id).values(**values)
    await session.execute(stmt)
    await session.commit()
    return await get_category_by_id_service(category_id, session)


async def delete_category_service(category_id: int, session: AsyncSession, user_id: int):
    _ = await get_category_by_id_service(category_id, session)
    stmt = (
        update(CourseCategory)
        .where(CourseCategory.category_id == category_id, CourseCategory.is_deleted == False)
        .values(is_deleted=True, deleted_by=user_id, deleted_at=datetime.utcnow())
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": 1, "message": "Category deleted"}


# ---------------- SUBCATEGORY SERVICES ----------------
async def create_subcategory_service(data, user_id: int, session: AsyncSession):
    # Ensure parent category exists and not deleted
    result = await session.execute(
        select(CourseCategory).where(CourseCategory.category_id == data.category_id, CourseCategory.is_deleted == False)
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found")

    new = CourseSubCategory(
        sub_category_name=data.sub_category_name,
        category_id=data.category_id,
        created_by=user_id,
        created_at=datetime.utcnow(),
        is_deleted=False,
    )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new


async def list_subcategories_service(session: AsyncSession, category_id: Optional[int] = None):
    q = select(CourseSubCategory).where(CourseSubCategory.is_deleted == False)
    if category_id is not None:
        q = q.where(CourseSubCategory.category_id == category_id)
    result = await session.execute(q)
    return result.scalars().all()


async def get_subcategory_by_id_service(sub_id: int, session: AsyncSession):
    result = await session.execute(
        select(CourseSubCategory).where(CourseSubCategory.sub_category_id == sub_id, CourseSubCategory.is_deleted == False)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found")
    return sub


async def update_subcategory_service(sub_id: int, data, user_id: int, session: AsyncSession):
    sub = await get_subcategory_by_id_service(sub_id, session)

    if getattr(data, "category_id", None) is not None:
        # verify category exists
        await get_category_by_id_service(data.category_id, session)

    values = {}
    if getattr(data, "sub_category_name", None) is not None:
        values["sub_category_name"] = data.sub_category_name
    if getattr(data, "category_id", None) is not None:
        values["category_id"] = data.category_id

    if not values:
        return sub

    values.update({"updated_by": user_id, "updated_at": datetime.utcnow()})
    stmt = update(CourseSubCategory).where(CourseSubCategory.sub_category_id == sub_id).values(**values)
    await session.execute(stmt)
    await session.commit()
    return await get_subcategory_by_id_service(sub_id, session)


async def delete_subcategory_service(sub_id: int, session: AsyncSession, user_id: int):
    _ = await get_subcategory_by_id_service(sub_id, session)
    stmt = (
        update(CourseSubCategory)
        .where(CourseSubCategory.sub_category_id == sub_id, CourseSubCategory.is_deleted == False)
        .values(is_deleted=True, deleted_by=user_id, deleted_at=datetime.utcnow())
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": 1, "message": "Subcategory deleted"}


# ---------------- COURSES SERVICES ----------------
async def create_course_service(data, user_id: int, session: AsyncSession):
    # ensure subcategory exists and not deleted
    result = await session.execute(
        select(CourseSubCategory).where(CourseSubCategory.sub_category_id == data.course_subcategory, CourseSubCategory.is_deleted == False)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found")

    new = Courses(
        course_name=data.course_name,
        course_link=str(data.course_link),
        course_subcategory=data.course_subcategory,
        created_by=user_id,
        created_at=datetime.utcnow(),
        is_deleted=False,
    )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new


async def list_courses_service(session: AsyncSession, sub_category_id: Optional[int] = None):
    q = select(Courses).where(Courses.is_deleted == False)
    if sub_category_id is not None:
        q = q.where(Courses.course_subcategory == sub_category_id)
    result = await session.execute(q)
    return result.scalars().all()


# async def list_courses_search_service(
#     sub_category_id: int | None,
#     search: str | None,
#     session: AsyncSession
# ):
#     query = select(Courses).where(Courses.is_deleted == False)

#     if sub_category_id:
#         query = query.where(Courses.course_subcategory == sub_category_id)

#     if search:
#         query = query.where(Courses.course_name.ilike(f"%{search}%"))  # case-insensitive partial match

#     result = await session.execute(query)
#     return result.scalars().all()


async def search_courses_service(search: str, session: AsyncSession):
    query = select(Courses).where(
        Courses.is_deleted == False,
        Courses.course_name.ilike(f"%{search}%")
    )

    result = await session.execute(query)
    return result.scalars().all()



async def get_course_by_id_service(course_id: int, session: AsyncSession):
    result = await session.execute(
        select(Courses).where(Courses.course_id == course_id, Courses.is_deleted == False)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


async def update_course_service(course_id: int, data, user_id: int, session: AsyncSession):
    course = await get_course_by_id_service(course_id, session)

    if getattr(data, "course_subcategory", None) is not None:
        # verify new subcategory exists
        await get_subcategory_by_id_service(data.course_subcategory, session)

    values = {}
    if getattr(data, "course_name", None) is not None:
        values["course_name"] = data.course_name
    if getattr(data, "course_link", None) is not None:
        values["course_link"] = str(data.course_link)
    if getattr(data, "course_subcategory", None) is not None:
        values["course_subcategory"] = data.course_subcategory

    if not values:
        return course

    values.update({"updated_by": user_id, "updated_at": datetime.utcnow()})
    stmt = update(Courses).where(Courses.course_id == course_id).values(**values)
    await session.execute(stmt)
    await session.commit()
    return await get_course_by_id_service(course_id, session)


async def delete_course_service(course_id: int, session: AsyncSession, user_id: int):
    _ = await get_course_by_id_service(course_id, session)
    stmt = (
        update(Courses)
        .where(Courses.course_id == course_id, Courses.is_deleted == False)
        .values(is_deleted=True, canceled_by=user_id, canceled_at=datetime.utcnow())
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": 1, "message": "Course deleted"}
