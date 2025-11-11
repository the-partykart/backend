from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.information_repository import check_all_information_db
from app.db.services.users_repository import async_create_user_db, check_username_db, delete_user_db, get_all_users_db, update_user_db
from app.microservices.common_function import object_to_dict
from app.utility.auth_utils import hashed_password
from app.utility.logging_utils import log_async, log


async def check_username_service(
        username, 
        session:AsyncSession
        ):
    try:
        result = await check_username_db(username=username, session=session)
        # data = [object_to_dict(result_data) for result_data in result]

        # Convert each part of the tuple (Users, UserRoles, Roles) to dict
        data = [
            {
                "user": object_to_dict(row[0]),
                "user_role": object_to_dict(row[1]),
                "role": object_to_dict(row[2])
            }
            for row in result
        ]
        if not data or data[0]["user"].get("email") is None:
            raise HTTPException(status_code=404, detail="Invalid Username")
        # if data["email"] is None or data is None:
        #     raise JSONResponse(content="Invalide Username",status_code=404) 
        return data


    except Exception as e:
        raise 
    

async def check_phone_no_service(
        phone_no: str,
        session: AsyncSession,
        background_tasks: BackgroundTasks
):
    try:
        result = await check_username_db(
            phone_no=phone_no,
            session=session,
            background_tasks=background_tasks
        )

        data = [
            {
                "user": await object_to_dict(row[0]),
                "user_role": await object_to_dict(row[1]),
                "role": await object_to_dict(row[2])
            }
            for row in result
        ]

        if not data or data[0]["user"].get("phone_no") is None:
            raise HTTPException(status_code=404, detail="Invalid Username")

        return data

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[USER_SERVICE][check_username] Error in User Login Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail="Invalid Username"
        )

async def create_user_logic(
        data,  
        user_id, 
        background_tasks: BackgroundTasks, 
        session: AsyncSession
        ):
    try:
        # password hashing
        password = str(data.password)
        hash_result = await hashed_password(password = password)
        if hash_result:
            password = hash_result
        if not hash_result or hash_result is None:
            password = "$2b$12$KcyZNprgkJr8uK/gcM/le.BpPPhGHxZLCWjalh9uzCKQ5D4kpFZOe"
        create_user = await async_create_user_db(
            background_tasks=background_tasks,
            session=session, 
            name=data.name, 
            email=data.email,
            phone_no=data.phone_no,
            business_name=data.business_name,
            password=password, 
            role=data.role,
            created_by=user_id
            )
        if create_user:
            return True
        else:
            raise HTTPException(
                detail="Unable to Register.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        log.error(f"Error in User registration {e}")
        return JSONResponse(content="Failed to User registration", status_code=500)
    

async def fetch_all_users_service(
        background_tasks:BackgroundTasks,
        session: AsyncSession
        ):
    try:
        users_result = await get_all_users_db(
            background_tasks=background_tasks,
            session=session
            )
        if users_result is not None:
            result = [await object_to_dict(users_result_obj) for users_result_obj in users_result]
            return {"status": 1, "message": result}
        else:
            return JSONResponse(content={"status": 0, "message": "No user found."})
    except Exception as e:
        return HTTPException(detail={
            "message":"Failed to retrieve users."
            }, status_code=404)
    


async def update_user_service(
        user_id,
        current_name,
        u_user_id,
        data, 
        background_tasks : BackgroundTasks,
        session: AsyncSession,
        ):
    """
    Handles the business logic for updating user details.
    """
    try:
        log_async(
            background_tasks,
            f"[SERVICE][UPDATE_USER] Attempting to update user {user_id} with new data.",
            "info"
        )
        name=data.name
        result = await update_user_db(
            background_tasks=background_tasks,
            name=name,
            session=session, 
            current_name = current_name,
            user_id=user_id,
            u_user_id=u_user_id,
            )
        if result:
            log_async(
                background_tasks,
                f"[SERVICE][UPDATE_USER] User {user_id} successfully updated by DB operation.",
                "info"
            )
            return True    
        else: 
            log_async(
                background_tasks,
                f"[SERVICE][UPDATE_USER] DB operation failed to update user {user_id}.",
                "warning"
            )
            return False
        
    except Exception as e:
        log_async(
            background_tasks,
            f"[SERVICE][UPDATE_USER] Error in update_user_service for user {user_id}: {str(e)}",
            "error"
        )
        # Re-raise the exception to be caught by the API handler, or raise a custom service error.
        raise Exception(f"Service error while updating user: {e}")



async def delete_user_service(
        target_user_id: int,
        user_id: int,
        background_tasks: BackgroundTasks,
        session: AsyncSession,
        ):
    """
    Handles the business logic for soft deleting a user.
    """
    try:
        result = await delete_user_db(
            target_user_id=target_user_id,
            deleted_by_user_id=user_id,
            session=session,
            background_tasks=background_tasks
        )
        if result is True: # `True` indicates successful deletion from DB layer
            log_async(
                background_tasks,
                f"[SERVICE][DELETE_USER] User ID {target_user_id} successfully soft-deleted by DB operation.",
                "info"
            )
            return {"status": "success", "message": f"User with ID {target_user_id} soft-deleted successfully."}
        elif result is False: # `False` indicates user not found/no rows affected from DB layer
            log_async(
                background_tasks,
                f"[SERVICE][DELETE_USER] Soft-delete failed for user ID {target_user_id}: User not found in DB or no change.",
                "error"
            )
            return {"status": "not_found", "message": f"User with ID {target_user_id} not found or already deleted."}
        else: # Catch any other unexpected return from DB layer
            log_async(
                background_tasks,
                f"[SERVICE][DELETE_USER] Unexpected result from DB operation for user ID {target_user_id}. Result: {result}",
                "error"
            )
            return {"status": "error", "message": f"Unexpected error during soft-deletion process."}

    except Exception as e:
        log_async(
            background_tasks,
            f"[SERVICE][DELETE_USER] Error in soft-delete service for user ID {target_user_id}: {str(e)}",
            "error",
            exc_info=True # Include traceback
        )
        # Re-raise the exception to be handled by the API layer
        raise Exception(f"Service error while soft-deleting user: {e}")
    

async def fetch_all_information_service(
        background_tasks:BackgroundTasks,
        session: AsyncSession
        ):
    try:
        data={}
        info_result = await check_all_information_db(
            background_tasks=background_tasks,
            session=session
            )
        if info_result is not None:
            result = [await object_to_dict(users_result_obj) for users_result_obj in info_result]
            for item in result:
                key_name = item["information_name"]
                data[key_name] = item
            return data
        else:
            return None
        
    except Exception as e:
        return HTTPException(detail={
            "message":"Failed to retrieve information."
            }, status_code=404)
    
