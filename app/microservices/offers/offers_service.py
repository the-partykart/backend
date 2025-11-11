from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.offers_repository import create_offer_db, delete_offer_db, get_all_offer_db, get_offer_db, update_offer_db
from app.microservices.common_function import object_to_dict
from app.utility.logging_utils import log_async 

from datetime import datetime



# Validation
async def check_offer_service(
        offer_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_offer_db(
            offer_id= offer_id,
            session=session,
            background_tasks=background_tasks,
        )

        if not result or result is None:
            raise HTTPException(detail="offer Not Found", status_code= status.HTTP_404_NOT_FOUND)
        elif result.offer_id and result.is_deleted==True:
            raise HTTPException(detail="offer Not Found (offer Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        else:
            return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create offer: {e}"
        )


async def create_offer_service(
        offer_name,
        offer_percentage,
        offer_description,
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await create_offer_db(
            offer_name = offer_name,
            offer_percentage = offer_percentage,
            offer_description =  offer_description,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return {
                "status":1,
                "message":"offer create successfully"
                }
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer_SERVICE][CREATE_offer_SERVICE] Error in create offer Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create offer: {e}"
        )

async def get_all_offer_service(
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_offer_db(
            session=session,
            background_tasks=background_tasks
            )
        
        if result:
            data = [await object_to_dict(result_data) for result_data in result]
            return data
        
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[offer][GET_ALL_offer] Error: Failed Logic to Fetch all offer. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all offer.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][GET_ALL_offer] Error: Failed to Fetch all offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all offer.")
    


async def get_offer_service(
        offer_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_offer_db(
            offer_id=offer_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result:
            # data = {
            #     col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
            #     for col in result.__table__.columns
            # }
            # return data
            data = {
            "offer_id": result.offer_id,
            "offer_name": result.offer_name,
            "offer_percentage" : result.offer_percentage,
            "created_by": result.created_by,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_by": result.updated_by,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            "is_deleted": result.is_deleted,
            "deleted_by": result.deleted_by,
            "deleted_at": result.deleted_at.isoformat() if result.deleted_at else None,
            }
            return data
        
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[offer][GET_offer] Error: Failed Logic to Fetch offer. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch offer.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][GET_ALL_offer] Error: Failed to Fetch offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch offer.{e}")


async def update_offer_service(
        offer_id,
        offer_name,
        offer_percentage,
        offer_description,
        user_id,
        current_offer_name,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await update_offer_db(
            offer_id = offer_id,
            offer_name=offer_name,
            offer_percentage=offer_percentage,
            offer_description=offer_description,
            current_offer_name=current_offer_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"offer Update successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer_SERVICE][CREATE_offer_SERVICE] Error in create offer Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create offer: {e}"
        )
    
async def delete_offer_service(
    offer_id,
    user_id,
    current_offer_name,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await delete_offer_db(
            offer_id = offer_id,
            current_offer_name=current_offer_name,
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
            message=f"[offer_SERVICE][DELETE_offer_SERVICE] Error in Delete offer Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete offer: {e}"
        )