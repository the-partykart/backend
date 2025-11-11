from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Roles, UserRoles, Users
from sqlalchemy import select, update
from sqlalchemy.sql import func
from typing import List, Optional
from app.utility.logging_utils import log, log_async
from fastapi import BackgroundTasks, HTTPException

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError


async def check_roles(
        session: AsyncSession,
        background_tasks = BackgroundTasks,
        ):
    try:
        result = await session.execute(select(Roles).where(Roles.role_name == "admin"))
        search_result = result.scalar_one_or_none()
        return search_result
    except Exception as e:
        # log_async(
        #     background_tasks,
        #     f"[DB][CHECK_ROLES] Error checking roles : {str(e)}",
        #     "error",
        #     always_sync=True
        # )
        return False


async def master_role(session: AsyncSession):
    try:
        new_role = Roles(role_name="admin", created_by=0)
        session.add(new_role)
        await session.commit()
        await session.refresh(new_role)
        result = new_role.role_id
        new_role_user = Roles(role_name="users", created_by=0)
        session.add(new_role_user)
        await session.commit()
        return result
    except Exception as e:
        return False
         

async def check_role_name_db(
        role_name: str,
        session: AsyncSession,
        background_tasks = BackgroundTasks,
        ):
    try:
        stmt = select(Roles).where(Roles.role_name==role_name)
        search_result = await session.execute(stmt)
        result = search_result.scalars().all()
        if result:
            return result
        else:
            return None
    except Exception as e:
        # log.error(f"error in fetch Role Name: {e}")
        return False
    

async def check_superadmin(session: AsyncSession):
    try:
        result = await session.execute(select(Users).where(Users.email == 'admin@sample.com'))
        search_result = result.scalar_one_or_none()
        return search_result

    except Exception as e:
        return False
    

async def user_role_entry(user_id, role_id, created_by, background_tasks: BackgroundTasks, session:AsyncSession):
    try:
        new_user_role = UserRoles(user_id=user_id, role_id=role_id,created_by=created_by)
        session.add(new_user_role)
        await session.commit()
        result = await session.refresh(new_user_role)
        new_user_role_id = new_user_role.user_role_id
        return True
    
    except Exception as e:
        return False
    
async def get_user_role_from_db(
    user_id,
    background_tasks: BackgroundTasks, 
    session:AsyncSession,
):
    try:
        result = await session.execute(select(UserRoles).where(UserRoles.user_id == user_id))
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        return False
    