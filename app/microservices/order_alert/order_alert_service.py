from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.cart_repository import add_cart_db, get_cart_db, get_all_cart_db, remove_cart_db, update_cart_db
from app.db.services.order_alert_repository import get_all_order_admin_db, get_all_order_db, get_order_id_db
from app.microservices.common_function import object_to_dict
from app.utility.logging_utils import log_async 

from datetime import datetime



# Validation
async def check_cart_service(
        cart_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_cart_db(
            cart_id= cart_id,
            session=session,
            background_tasks=background_tasks,
        )

        if not result or result is None:
            raise HTTPException(detail="cart Not Found", status_code= status.HTTP_404_NOT_FOUND)
        elif result.cart_id and result.is_canceled==True:
            raise HTTPException(detail="cart Not Found (cart Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        else:
            return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create cart: {e}"
        )


async def add_cart_service(
        product_id,
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await add_cart_db(
            product_id=product_id,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"cart create successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart_SERVICE][CREATE_cart_SERVICE] Error in create cart Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create cart: {e}"
        )

async def get_all_order_service(
        user_id,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_order_db(
            user_id=user_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result is None or len(result)<=0:
            return None
        
        if result:
            data = [await object_to_dict(result_data) for result_data in result]
            return data
        
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[cart][GET_ALL_cart] Error: Failed Logic to Fetch all cart. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all cart.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][GET_ALL_cart] Error: Failed to Fetch all cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all cart.")
    


async def get_all_order_admin_service(
        user_id,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_order_admin_db(
            user_id=user_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result is None or len(result)<=0:
            return None
        
        if result:
            data = [await object_to_dict(result_data) for result_data in result]
            return data
        
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[cart][GET_ALL_cart] Error: Failed Logic to Fetch all order. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all cart.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][GET_ALL_cart] Error: Failed to Fetch all cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all cart.")
    


async def get_order_id_service(
        order_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_order_id_db(
            order_id=order_id,
            session=session,
            background_tasks=background_tasks
            )
        
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
                message=f"[cart][GET_cart] Error: Failed Logic to Fetch cart. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch cart.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][GET_ALL_cart] Error: Failed to Fetch cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch cart.{e}")


async def update_cart_service(
        cart_id,
        cart_name,
        cart_image,
        user_id,
        current_cart_name,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await update_cart_db(
            cart_id = cart_id,
            cart_name=cart_name,
            cart_image=cart_image,
            current_cart_name=current_cart_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"cart Update successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart_SERVICE][CREATE_cart_SERVICE] Error in create cart Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create cart: {e}"
        )
    
async def remove_cart_service(
    cart_id,
    user_id,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await remove_cart_db(
            cart_id = cart_id,
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
            message=f"[cart_SERVICE][DELETE_cart_SERVICE] Error in Delete cart Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete cart: {e}"
        )
    