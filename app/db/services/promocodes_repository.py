from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Promocodes, Roles, UserRoles, Users
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


async def create_promocode_db(
        promocode_name,
        promocode_percentage,
        promocode_description,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_promocode = Promocodes(
            promocode_name=promocode_name, 
            promocode_percentage=promocode_percentage,
            promocode_description=promocode_description,
            created_by=user_id
            )
        session.add(new_promocode)
        await session.commit()
        result = await session.refresh(new_promocode)
        if new_promocode.promocode_id:
            new_promocode_id = new_promocode.promocode_id
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="promocode created",
                log_description=f"promocode Created by user_id {user_id}",
                previous_value=None,
                updated_value=promocode_name,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_promocode] Error Creating promocode {promocode_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating promocode: {e}")

        return False
    

async def check_promocode_name_db(
        promocode_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(Promocodes).where(Promocodes.promocode_name == promocode_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_promocode_NAME_DB] Error Checking promocode Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_promocode_db(
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Promocodes)
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_promocode] Error in Fetch All promocode.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_promocode_db(
        promocode_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Promocodes).where(Promocodes.promocode_id==promocode_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_promocode] Error in Fetch promocode.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
    
async def update_promocode_db(
        promocode_id:int,
        promocode_name:str,
        promocode_percentage,
        promocode_description,
        user_id : int,
        current_promocode_name: str,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        data = {}
        if promocode_name:
            data["promocode_name"] = promocode_name
        if promocode_percentage:
            data["promocode_percentage"] = promocode_percentage
        if promocode_description:
            data["promocode_description"] = promocode_description
        data["updated_by"] = user_id
        data["updated_at"] = func.now()

        stmt = update(Promocodes).where(Promocodes.promocode_id==promocode_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        update_result = result.rowcount
        if update_result==1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="promocode Updated",
                log_description=f"promocode Updated by user_id {user_id}",
                previous_value=current_promocode_name,
                updated_value=f"{data}",
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
            f"[DB][UPDATE_promocode] Error in Updating promocode {current_promocode_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating promocode: {e}")

        return False
    

async def delete_promocode_db(   
        promocode_id:int,
        current_promocode_name:str,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_deleted"] = True
        data["deleted_by"] = user_id
        data["deleted_at"] = func.now()
        stmt = update(Promocodes).where(Promocodes.promocode_id==promocode_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        promocode_result = result.rowcount
        if promocode_result != 1:
            return False
        if promocode_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="promocode Deleted",
                log_description=f"promocode with promocode id {promocode_id} deleted by user_id {user_id}",
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
            f"[DB][DELETE_promocode] Error in Delete promocode {current_promocode_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    