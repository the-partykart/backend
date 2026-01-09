from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.category_repository import create_category_db, create_sub_category_db, delete_sub_category_db, get_all_sub_category_db, get_category_db, delete_category_db, get_all_category_db, get_category_details_db, get_sub_category_db, update_category_db, update_sub_category_db
from app.microservices.common_function import object_to_dict
from app.utility.logging_utils import log_async 

from datetime import datetime



# Validation
async def check_category_service(
        category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_category_db(
            category_id= category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if not result or result is None:
            raise HTTPException(detail="category Not Found", status_code= status.HTTP_404_NOT_FOUND)
        elif result.category_id and result.is_deleted==True:
            raise HTTPException(detail="category Not Found (category Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        else:
            return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create category: {e}"
        )


async def create_category_service(
        category_name,
        category_image,
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await create_category_db(
            category_name = category_name,
            category_image=category_image,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"category create successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category_SERVICE][CREATE_category_SERVICE] Error in create category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create category: {e}"
        )

async def get_all_category_service(
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_category_db(
            session=session,
            background_tasks=background_tasks
            )
        
        # Guard against wrong return type
        if not result:
            return []

        if isinstance(result, bool):
            raise ValueError("DB function returned bool instead of list")
        
        if result:
            data = [await object_to_dict(result_data) for result_data in result]
            return data
        
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[category][GET_ALL_category1] Error: Failed Logic to Fetch all category. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all category.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category2] Error: Failed to Fetch all category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all category.")
    


async def get_category_service(
        category_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_category_db(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result is None or len(result)<1:
            return None
        
        if result:
            data = {
                col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
                for col in result.__table__.columns
            }
            return data
            # return result
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[category][GET_category] Error: Failed Logic to Fetch category. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch category.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category3] Error: Failed to Fetch category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch category.{e}")


async def update_category_service(
        category_id,
        category_name,
        category_image,
        user_id,
        current_category_name,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await update_category_db(
            category_id = category_id,
            category_name=category_name,
            category_image=category_image,
            current_category_name=current_category_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"category Update successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category_SERVICE][CREATE_category_SERVICE] Error in create category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create category: {e}"
        )
    
async def delete_category_service(
    category_id,
    user_id,
    current_category_name,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await delete_category_db(
            category_id = category_id,
            current_category_name=current_category_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return True
        
        else:
            return False
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category_SERVICE][DELETE_category_SERVICE] Error in Delete category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete category: {e}"
        )
    

async def get_category_details_service(
        category_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        
        result = await get_category_details_db(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if len(result) < 1:
            return None
        if result:
            # data = {
            #     col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
            #     for col in result.__table__.columns
            # }

            data = [await object_to_dict(result_data) for result_data in result]
            return data
            # return result
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[category][GET_category] Error: Failed Logic to Fetch category. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch category.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category4] Error: Failed to Fetch category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch category.{e}")




####  ========== sub category ===========



async def create_sub_category_service(
        sub_category_name,
        category_id,
        sub_category_image,
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await create_sub_category_db(
            sub_category_name = sub_category_name,
            sub_category_image = sub_category_image,
            category_id=category_id,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            # map_category = await map_category_db(
            #     category_id=category_id,
            #     sub_category_id = result,
            #     user_id = user_id,
            #     session = session,
            #     background_tasks = background_tasks,
            # )
            return{"status":1,"message":"sub_category create successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category_SERVICE][CREATE_sub_category_SERVICE] Error in create sub_category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create sub_category: {e}"
        )


async def get_all_sub_category_service(
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_sub_category_db(
            session=session,
            background_tasks=background_tasks
            )
        
        if result is None or len(result) < 1:
            return None
        
        if result:
            data = [await object_to_dict(result_data) for result_data in result]
            return data
        
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[sub_category][GET_ALL_sub_category] Error: Failed Logic to Fetch all sub_category. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all sub_category.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][GET_ALL_sub_category] Error: Failed to Fetch all sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all sub_category.")
    

async def get_sub_category_service(
        sub_category_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_sub_category_db(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result:
            data = {
                col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
                for col in result.__table__.columns
            }
            return data
            # return result
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[sub_category][GET_sub_category] Error: Failed Logic to Fetch sub_category. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch sub_category.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][GET_ALL_sub_category] Error: Failed to Fetch sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch sub_category.{e}")


async def check_sub_category_service(
        sub_category_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_sub_category_db(
            sub_category_id= sub_category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if not result or result is None:
            raise HTTPException(detail="sub_category Not Found", status_code= status.HTTP_404_NOT_FOUND)
        elif result.category_id and result.is_deleted==True:
            raise HTTPException(detail="sub_category Not Found (sub_category Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        else:
            return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in sub_category: {e}"
        )
    


async def update_sub_category_service(
        sub_category_id,
        category_id,
        sub_category_name,
        sub_category_image,
        user_id,
        current_sub_category_name,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await update_sub_category_db(
            sub_category_id = sub_category_id,
            category_id=category_id,
            sub_category_name=sub_category_name,
            sub_category_image=sub_category_image,
            current_sub_category_name=current_sub_category_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"sub_category Update successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category_SERVICE][CREATE_sub_category_SERVICE] Error in update sub_category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in update sub_category: {e}"
        )
    


async def delete_sub_category_service(
    sub_category_id,
    user_id,
    current_sub_category_name,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await delete_sub_category_db(
            sub_category_id = sub_category_id,
            current_sub_category_name=current_sub_category_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return True
        
        else:
            return False
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category_SERVICE][DELETE_sub_category_SERVICE] Error in Delete sub_category Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete sub_category: {e}"
        )