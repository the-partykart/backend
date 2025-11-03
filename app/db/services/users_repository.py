from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Roles, UserRoles, Users 
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


# async def check_username_db(session)


async def async_create_user_db(
        phone_no,
        business_name,
        session:AsyncSession, 
        name:str, 
        email:str, 
        password:str, 
        role:int, 
        created_by:int,
        background_tasks: BackgroundTasks):
    try:
        new_user = Users(
            name=name, 
            email=email, 
            password=password,
            phone_no=phone_no,
            business_name=business_name,
            created_by=created_by
            )
        session.add(new_user)
        await session.commit()
        result = await session.refresh(new_user)
        if new_user.user_id:
            new_user_id = new_user.user_id
            user_role = await user_role_entry(
                user_id=new_user_id, 
                role_id=role, 
                session=session,
                created_by=created_by,
                background_tasks=background_tasks)
            if user_role == False:
                return False
            if user_role:
                log_entry_result = await log_entry(
                    background_tasks=background_tasks,
                    session=session,
                    log_name="Job created",
                    log_description=f"New user created by user_id {created_by}",
                    previous_value=None,
                    updated_value=email,
                    changed_by=1)
                if log_entry_result:
                    return True
            return True
        
    except Exception as e:
        return False



async def check_username_db(
        phone_no: str,
        session: AsyncSession,
        background_tasks: BackgroundTasks
):
    try:
        stmt = (
            select(Users, UserRoles, Roles)
            .join(UserRoles, Users.user_id == UserRoles.user_id)
            .join(Roles, UserRoles.role_id == Roles.role_id)
            .where(Users.phone_no == phone_no)
        )
        result = await session.execute(stmt)
        return result.all()  # full row tuples
    except Exception as e:
        # Optionally log the error here
        return []
    
async def check_phone_no_db(
        phone_no,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        stmt = select(Users).where(Users.phone_no==phone_no)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        if search_result:
            return result
    except Exception as e:
        return False


async def get_user_by_id_db(
        user_id,
        background_tasks: BackgroundTasks,
        session: AsyncSession,
        ):
    """
    Retrieves a user from the database by their user ID.
    """
    try:
        stmt = select(Users).where(Users.user_id==user_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        # return searach_result
        if search_result:
            log_async(
                background_tasks,
                f"[DB][GET_USER] User with ID {user_id} found.",
                "info"
            )
            return search_result
        else:
            log_async(
                background_tasks,
                f"[DB][GET_USER] User with ID {user_id} not found in DB.",
                "info"
            )
            return None
    
    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_USER] Error fetching user with ID {user_id}: {str(e)}",
            "error",
            always_sync=True
        )
        raise Exception(f"Database error while fetching user: {e}") 
    

async def get_all_users_db(
        session : AsyncSession,
        background_tasks: BackgroundTasks):
    try:
        stmt = select(Users)
        result = await session.execute(stmt)
        users = result.scalars().all()
        return users
    
    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_USER] Error fetching user with ID: {str(e)}",
            "error",
            always_sync=True
        )
        raise Exception(f"Database error while fetching user: {e}") 



async def update_user_db(
        background_tasks : BackgroundTasks,
        current_name,
        u_user_id: int,
        session: AsyncSession, 
        user_id : int, 
        name: str = "None Name",
        ):
    """
    Performs the database operation to update user details.
    """
    try: 
        data = {}
        if name is not None:
            data["name"] = name
        data["updated_by"] = user_id
        data["updated_at"] = func.now()

        stmt = update(Users).where(Users.user_id==u_user_id).values(**data)
        result = await session.execute(stmt)  
        await session.commit()    # TODO what about commit
        update_result = result.rowcount
        if update_result == 1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="User Updated",
                log_description=f"user Updated by user_id {user_id}",
                previous_value=current_name,
                updated_value=name,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return None
    
    except Exception as e:
        await session.rollback()
        log_async(
            background_tasks,
            f"[DB][UPDATE_USER_DB] Database error during user update for ID {user_id}: {str(e)}",
            "error",
            always_sync=True
        )
        raise Exception(f"Database error during user update: {e}")
    

async def delete_user_db(
        deleted_by_user_id: int,
        target_user_id: int,
        session: AsyncSession, 
        background_tasks: BackgroundTasks,
        ):
    """
    Performs the database operation to soft delete a user.
    Sets 'is_deleted' flag to True and records 'deleted_by'.
    """
    try:
        stmt = update(Users).where(Users.user_id == target_user_id).values(
                    is_deleted=True,
                    deleted_by=deleted_by_user_id,
                    deleted_at=func.now() # Assuming you have a deleted_at column
                )   
        result = await session.execute(stmt) 
        await session.commit()
        delete_result = result.rowcount
        if delete_result == 1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="User Delete",
                log_description=f"User {target_user_id}: Deleted by user_id {deleted_by_user_id}",
                previous_value=None,
                updated_value="Deleted",
                changed_by=deleted_by_user_id)
            if log_entry_result:
                return True
            return True
        else:
            return None

    except Exception as e:
        await session.rollback() # Rollback on error
        log_async(
            background_tasks,
            f"[DB][DELETE_USER_DB] Database error during soft-deletion of user ID {target_user_id}: {str(e)}", # Corrected typo
            "error",
            always_sync=True 
        )
        raise HTTPException(f"Database error during soft-deleting user: {e}")



async def check_userid_db(
        phone_no: str,
        session: AsyncSession,
        background_tasks: BackgroundTasks
):
    try:
        stmt = select(Users).where(Users.phone_no == phone_no)
        result = await session.execute(stmt)
        return result.scalars().first() 
     
    except Exception as e:
        # Optionally log the error here
        return None