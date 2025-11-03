from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Offers, Roles, UserRoles, Users
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


async def create_offer_db(
        offer_name,
        offer_percentage,
        offer_description,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_offer = Offers(
            offer_name=offer_name, 
            offer_percentage=offer_percentage,
            offer_description=offer_description,
            created_by=user_id
            )
        session.add(new_offer)
        await session.commit()
        result = await session.refresh(new_offer)
        if new_offer.offer_id:
            new_offer_id = new_offer.offer_id
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="offer created",
                log_description=f"offer Created by user_id {user_id}",
                previous_value=None,
                updated_value=offer_name,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_offer] Error Creating offer {offer_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating offer: {e}")

        return False
    

async def check_offer_name_db(
        offer_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(Offers).where(Offers.offer_name == offer_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_offer_NAME_DB] Error Checking offer Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_offer_db(
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Offers)
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_offer] Error in Fetch All offer.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_offer_db(
        offer_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Offers).where(Offers.offer_id==offer_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_offer] Error in Fetch offer.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
    
async def update_offer_db(
        offer_id:int,
        offer_name:str,
        offer_percentage,
        offer_description,
        user_id : int,
        current_offer_name: str,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        data = {}
        if offer_name:
            data["offer_name"] = offer_name
        if offer_percentage:
            data["offer_percentage"] = offer_percentage
        if offer_description:
            data["offer_description"] = offer_description
        data["updated_by"] = user_id
        data["updated_at"] = func.now()

        stmt = update(Offers).where(Offers.offer_id==offer_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        update_result = result.rowcount
        if update_result==1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="offer Updated",
                log_description=f"offer Updated by user_id {user_id}",
                previous_value=current_offer_name,
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
            f"[DB][UPDATE_offer] Error in Updating offer {current_offer_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating offer: {e}")

        return False
    

async def delete_offer_db(   
        offer_id:int,
        current_offer_name:str,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_deleted"] = True
        data["deleted_by"] = user_id
        data["deleted_at"] = func.now()
        stmt = update(Offers).where(Offers.offer_id==offer_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        offer_result = result.rowcount
        if offer_result != 1:
            return False
        if offer_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="offer Deleted",
                log_description=f"offer with offer id {offer_id} deleted by user_id {user_id}",
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
            f"[DB][DELETE_offer] Error in Delete offer {current_offer_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    