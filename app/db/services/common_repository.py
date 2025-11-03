from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Users, Log
# from app.db.db_session import async_session_maker 
from sqlalchemy import select, update
from sqlalchemy.sql import func
from typing import List, Optional
from app.db.services.roles_repository import user_role_entry
from app.utility.logging_utils import log, log_async
from fastapi import BackgroundTasks, HTTPException

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError





async def log_entry(
        session: AsyncSession, 
        background_tasks:BackgroundTasks,
        log_name: str, 
        changed_by: int,
        log_description: str=None, 
        previous_value: str=None, 
        updated_value: str=None
        ):
    try:
    # log_name =  
    # log_description = 
    # previous_value =  
    # updated_value =  
    # changed_by =  
    # changed_at =  

        new_log = Log(
            log_name=log_name,
            log_description=log_description,
            previous_value=previous_value,
            updated_value=updated_value,
            changed_by=changed_by,
        )

        session.add(new_log)
        await session.commit()
        await session.refresh(new_log)

        if new_log.log_id:
            return True
        else:
            False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][LOG_ENTRY] Error in log entry : {str(e)}",
            "error",
            always_sync=True
        )
        return False
    


async def get_user_from_db(phone_no, session:AsyncSession):
    try:
        stmt = select(Users).where(Users.phone_no==phone_no)
        result = await session.execute(stmt)
        search_result = result.scalar_one_or_none() 
        if search_result:
            return search_result
        else:
            return False
    except Exception as e:
        return False