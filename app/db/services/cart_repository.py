from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import  Cart, Categary, Roles, UserRoles, Users 
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


async def add_cart_db(
        product_id,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_cart = Cart(
            product_id=product_id,
            user_id=user_id,
            created_by=user_id
            )
        session.add(new_cart)
        await session.commit()
        result = await session.refresh(new_cart)
        if new_cart.cart_id:
            new_cart_id = new_cart.cart_id
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="cart created",
                log_description=f"cart Created by user_id {user_id}",
                previous_value=None,
                updated_value=product_id,
                changed_by=user_id)
            if log_entry_result:
                return True
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_cart] Error Creating cart {product_id}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating cart: {e}")

        return False
    

async def check_cart_name_db(
        cart_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(Categary).where(Categary.cart_name == cart_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_cart_NAME_DB] Error Checking cart Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_cart_db(
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Cart).where((Cart.user_id==user_id) & (Cart.is_canceled==False))
        result = await session.execute(stmt)
        search_result = result.scalars().all()
        return search_result


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_cart] Error in Fetch All cart.: {str(e)}",
            "error",
            always_sync=True
        )
        return None
    

async def get_cart_db(
        cart_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(Cart).where(Cart.cart_id==cart_id)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_cart] Error in Fetch cart.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    
    
async def update_cart_db(
        cart_id:int,
        cart_name:str,
        cart_image,
        user_id : int,
        current_cart_name: str,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        data = {}
        if cart_name:
            data["cart_name"] = cart_name
        if cart_image:
            data["cart_image"] = cart_image
        data["updated_at"] = func.now()

        stmt = update(Categary).where(Categary.cart_id==cart_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        update_result = result.rowcount
        if update_result==1:
            log_entry_result = await log_entry(
                background_tasks=background_tasks,
                session=session,
                log_name="cart Updated",
                log_description=f"cart Updated by user_id {user_id}",
                previous_value=current_cart_name,
                updated_value=cart_name,
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
            f"[DB][UPDATE_cart] Error in Updating cart {current_cart_name}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating cart: {e}")

        return False
    

async def remove_cart_db(   
        cart_id:int,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_canceled"] = True
        data["canceled_by"] = user_id
        data["canceled_at"] = func.now()
        stmt = update(Cart).where(Cart.cart_id==cart_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        cart_result = result.rowcount
        if cart_result != 1:
            return False
        if cart_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="cart Deleted",
                log_description=f"cart with cart id {cart_id} deleted by user_id {user_id}",
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
            f"[DB][DELETE_cart] Error in Delete cart {current_cart_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

# async def check_available_cart(
#     cart_id:int,
#     session: AsyncSession,
#     background_tasks : BackgroundTasks,  
# ):
#     try:
#         stmt = select

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][cart_AVAILABLE] Error in Search cart Availability {cart_id}: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False

