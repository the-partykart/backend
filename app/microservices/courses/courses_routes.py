# app/microservices/courses/courses_routes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.microservices.common_function import get_current_user, get_current_role
from app.db.models.db_base import Users

from app.microservices.courses.courses_schema import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse,
    CourseCreate, CourseUpdate, CourseResponse
)

from app.microservices.courses.courses_service import (
    create_category_service, list_categories_service, get_category_by_id_service, search_courses_service,
    update_category_service, delete_category_service,

    create_subcategory_service, list_subcategories_service,
    get_subcategory_by_id_service, update_subcategory_service,
    delete_subcategory_service,

    create_course_service, list_courses_service,
    get_course_by_id_service, update_course_service,
    delete_course_service
)

prefix = "v1"  # your current prefix
router = APIRouter(prefix=f"/{prefix}/courses", tags=["courses"])



@router.get("/search", response_model=list[CourseResponse])
async def search_courses(
    search: str,
    session: AsyncSession = Depends(get_async_session)
):
    return await search_courses_service(search, session)



# ---------- CATEGORY ----------
@router.post("/category", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    # admin check
    await get_current_role(user.user_id, background_tasks, session)
    return await create_category_service(data, user.user_id, session)


@router.get("/category", response_model=List[CategoryResponse])
async def list_categories(session: AsyncSession = Depends(get_async_session)):
    return await list_categories_service(session)


@router.get("/category/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, session: AsyncSession = Depends(get_async_session)):
    return await get_category_by_id_service(category_id, session)


@router.patch("/category/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await update_category_service(category_id, data, session, user.user_id)


@router.delete("/category/{category_id}")
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await delete_category_service(category_id, session, user.user_id)


# ---------- SUBCATEGORY ----------
@router.post("/subcategory", response_model=SubCategoryResponse)
async def create_subcategory(
    data: SubCategoryCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await create_subcategory_service(data, user.user_id, session)


@router.get("/subcategory", response_model=List[SubCategoryResponse])
async def list_subcategories(
    category_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session)
):
    return await list_subcategories_service(session, category_id)


@router.get("/subcategory/{sub_id}", response_model=SubCategoryResponse)
async def get_subcategory(sub_id: int, session: AsyncSession = Depends(get_async_session)):
    return await get_subcategory_by_id_service(sub_id, session)


@router.patch("/subcategory/{sub_id}", response_model=SubCategoryResponse)
async def update_subcategory(
    sub_id: int,
    data: SubCategoryUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await update_subcategory_service(sub_id, data, user.user_id, session)


@router.delete("/subcategory/{sub_id}")
async def delete_subcategory(
    sub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await delete_subcategory_service(sub_id, session, user.user_id)


# ---------- COURSES ----------
@router.post("/create", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await create_course_service(data, user.user_id, session)


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    sub_category_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session)
):
    return await list_courses_service(session, sub_category_id)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, session: AsyncSession = Depends(get_async_session)):
    return await get_course_by_id_service(course_id, session)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await update_course_service(course_id, data, user.user_id, session)


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    await get_current_role(user.user_id, background_tasks, session)
    return await delete_course_service(course_id, session, user.user_id)

