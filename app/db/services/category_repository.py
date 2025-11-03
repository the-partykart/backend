from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import  Categary, CategaryMapping, Roles, SubCategary, UserRoles, Users 
from sqlalchemy import select, update
from sqlalchemy.sql import func
from typing import List, Optional
from app.db.services.common_repository import log_entry
from app.db.services.roles_repository import user_role_entry
from app.utility.logging_utils import log, log_async
from fastapi import BackgroundTasks, HTTPException

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError


async def create_category_db(
        category_name,
        category_image,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_category = Categary(
            category_name=category_name,
            category_image=category_image,
            created_by=user_id
            )
        session.add(new_category)
        await session.commit()
        result = await session.refresh(new_category)
        if new_category.category_id:
            new_category_id = new_category.category_id
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="category created",
                log_description=f"category Created by user_id {user_id}",
                previous_value=None,
                updated_value=category_name,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_category] Error Creating category {category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating category: {e}")

        return False
    

async def check_category_name_db(
        category_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(Categary).where(Categary.category_name == category_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_category_NAME_DB] Error Checking category Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_category_db(
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Categary).where(Categary.is_deleted==0)
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch All category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_category_db(
        category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Categary).where(Categary.category_id==category_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
    
async def update_category_db(
        category_id:int,
        category_name:str,
        category_image,
        user_id : int,
        current_category_name: str,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        data = {}
        if category_name:
            data["category_name"] = category_name
        if category_image:
            data["category_image"] = category_image
        data["updated_at"] = func.now()

        stmt = update(Categary).where(Categary.category_id==category_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        update_result = result.rowcount
        if update_result==1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="category Updated",
                log_description=f"category Updated by user_id {user_id}",
                previous_value=current_category_name,
                updated_value=category_name,
                changed_by=user_id
                )
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][UPDATE_category] Error in Updating category {current_category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating category: {e}")

        return False
    

async def delete_category_db(   
        category_id:int,
        current_category_name:str,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_deleted"] = True
        data["deleted_by"] = user_id
        data["deleted_at"] = func.now()
        stmt = update(Categary).where(Categary.category_id==category_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        category_result = result.rowcount
        if category_result != 1:
            return False
        if category_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="category Deleted",
                log_description=f"category with category id {category_id} deleted by user_id {user_id}",
                previous_value="is_deleted=0",
                updated_value="is_deleted=1",
                changed_by=user_id
                )
            if log_entry_result:
                return True
            return True

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][DELETE_category] Error in Delete category {current_category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_category_details_db(
        category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(SubCategary).where((SubCategary.category_id==category_id)&(SubCategary.is_deleted==0))
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
####  ========== sub category ===========

async def check_sub_category_name_db(
        sub_category_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(SubCategary).where(SubCategary.sub_category_name == sub_category_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_category_NAME_DB] Error Checking category Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def create_sub_category_db(
        sub_category_name,
        category_id,
        sub_category_image,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_category = SubCategary(
            sub_category_name=sub_category_name,
            sub_category_image=sub_category_image,
            category_id = category_id,
            created_by=user_id
            )
        session.add(new_category)
        await session.commit()
        result = await session.refresh(new_category)
        if new_category.category_id:
            new_category_id = new_category.sub_category_id
            map_category = await map_category_db(
                category_id=category_id,
                sub_category_id = new_category_id,
                user_id = user_id,
                session = session,
                background_tasks = background_tasks,
            )
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="sub_category created",
                log_description=f"sub_category Created by user_id {user_id}",
                previous_value=None,
                updated_value=sub_category_name,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_category] Error Creating category {sub_category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating category: {e}")

        return False
    

async def map_category_db(
        category_id,
        sub_category_id,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        map_category = CategaryMapping(
            category_id=category_id,
            sub_category_id=sub_category_id,
            created_by=user_id
            )
        session.add(map_category)
        await session.commit()
        result = await session.refresh(map_category)
        if result:
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_category] Error mapping Creating category {sub_category_id}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating category: {e}")

        return False
    

async def get_sub_category_db(
        sub_category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(SubCategary).where(SubCategary.sub_category_id==sub_category_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_sub_category_db(
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(SubCategary)
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch All category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    


async def get_sub_category_db(
        sub_category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(SubCategary).where(SubCategary.sub_category_id==sub_category_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_category] Error in Fetch category.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    


async def update_sub_category_db(
        sub_category_id:int,
        category_id,
        sub_category_name:str,
        sub_category_image,
        user_id : int,
        current_sub_category_name: str,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        data = {}
        if sub_category_name:
            data["sub_category_name"] = sub_category_name
        if sub_category_image:
            data["sub_category_image"] = sub_category_image
        if category_id:
            data["category_id"] = category_id

        data["updated_at"] = func.now()

        stmt = update(SubCategary).where(SubCategary.sub_category_id==sub_category_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        update_result = result.rowcount
        if update_result==1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="sub_category Updated",
                log_description=f"sub_category Updated by user_id {user_id}",
                previous_value=current_sub_category_name,
                updated_value=sub_category_name,
                changed_by=user_id
                )
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][UPDATE_sub_category] Error in Updating sub_category {current_sub_category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating category: {e}")

        return False


async def delete_sub_category_db(   
        sub_category_id:int,
        current_sub_category_name:str,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_deleted"] = True
        data["deleted_by"] = user_id
        data["deleted_at"] = func.now()
        stmt = update(SubCategary).where(SubCategary.sub_category_id==sub_category_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        sub_category_result = result.rowcount
        if sub_category_result != 1:
            return False
        if sub_category_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="sub_category Deleted",
                log_description=f"sub_category with category id {sub_category_id} deleted by user_id {user_id}",
                previous_value="is_deleted=0",
                updated_value="is_deleted=1",
                changed_by=user_id
                )
            if log_entry_result:
                return True
            return True

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][DELETE_sub_category] Error in Delete category {current_sub_category_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
