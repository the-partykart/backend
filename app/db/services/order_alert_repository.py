from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import OrderAlert, Products, Roles, UserRoles, Users ,BuyProducts
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
from sqlalchemy.orm import selectinload


async def new_order_db(
        order_id,
        buy_product_id,
        total_amount,
        shipping_details,
        user_id,
        session: AsyncSession,
        background_tasks : BackgroundTasks,
):
    try:
        new_order = OrderAlert(
            order_id = order_id,
            buy_product_id = buy_product_id,
            total_amount =total_amount,
            delivery_status = "Undelivered",
            shipping_details = shipping_details or {},
            created_by = user_id
            )
        session.add(new_order)
        await session.commit()
        result = await session.refresh(new_order)
        return True


    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_order_alert] Error Creating Order Alert {buy_product_id}: {str(e)}",
            "error",
            always_sync=True
        )
        # raise HTTPException(
        #     detail=f"Database error Error Creating product: {e}")

        return False
    




# async def add_cart_db(
#         product_id,
#         user_id,
#         session: AsyncSession,
#         background_tasks : BackgroundTasks,
# ):
#     try:
#         new_cart = Cart(
#             product_id=product_id,
#             user_id=user_id,
#             created_by=user_id
#             )
#         session.add(new_cart)
#         await session.commit()
#         result = await session.refresh(new_cart)
#         if new_cart.cart_id:
#             new_cart_id = new_cart.cart_id
#             log_entry_result = await log_entry(
#                 background_tasks=background_tasks,
#                 session=session,
#                 log_name="cart created",
#                 log_description=f"cart Created by user_id {user_id}",
#                 previous_value=None,
#                 updated_value=product_id,
#                 changed_by=user_id)
#             if log_entry_result:
#                 return True
#             return True
#         else:
#             return False

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][CREATE_cart] Error Creating cart {product_id}: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         # raise HTTPException(
#         #     detail=f"Database error Error Creating cart: {e}")

#         return False
    

# async def check_cart_name_db(
#         cart_name: str,
#         session: AsyncSession,
#         background_tasks :BackgroundTasks,
# ):
#     try:
#         stmt = select(Categary).where(Categary.cart_name == cart_name)
#         result = await session.execute(stmt)
#         search_result = result.scalars().first()
#         return search_result

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][CHECK_cart_NAME_DB] Error Checking cart Name: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False
    

async def get_all_order_db(
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(OrderAlert).where((OrderAlert.created_by==user_id))
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
    


async def get_all_order_admin_db(
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(OrderAlert)
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
    


async def get_order_id_db(
        order_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        stmt = select(BuyProducts).where(BuyProducts.order_id==order_id)
        result = await session.execute(stmt)
        search_result = result.scalars().all()
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





# async def check_product_name_db(
#         product_name: str,
#         session: AsyncSession,
#         background_tasks :BackgroundTasks,
# ):
#     try:
#         stmt = select(Products).where(Products.product_name == product_name)
#         result = await session.execute(stmt)
#         search_result = result.scalars().first()
#         return search_result

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][CHECK_product_NAME_DB] Error Checking product Name: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False
    
# async def get_all_buy_product_db(
#     session: AsyncSession,
#     background_tasks: BackgroundTasks,
# ):
#     try:
#         stmt = select(BuyProducts)
#         result = await session.execute(stmt)
#         data = result.scalars().all()

#         # data = [
#         #     {
#         #         "product_id": row.product_id,
#         #         "product_name": row.product_name,
#         #         "product_price": row.product_price,
#         #         "product_description": row.product_description,
#         #         "created_by": row.created_by,
#         #         "created_at": row.created_at.isoformat() if row.created_at else None,
#         #         "updated_by": row.updated_by,
#         #         "updated_at": row.updated_at.isoformat() if row.updated_at else None,
#         #         "is_deleted": row.is_deleted,
#         #         "deleted_by": row.deleted_by,
#         #         "deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
#         #     }
#         #     for row in companies
#         # ]

#         return data

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][GET_ALL_product] Error in Fetch All product: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False


# async def get_buy_product_db(
#         buy_product_id: int,
#         session: AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         # stmt = select(product).where(product.product_id==product_id)
#         stmt = select(BuyProducts).where(BuyProducts.buy_product_id==buy_product_id)
#         result = await session.execute(stmt)
#         product = result.scalars().first()

#         # data = {
#         #     "product_id": companies.product_id,
#         #     "product_name": companies.product_name,
#         #     "sector_id": companies.sector_id,
#         #     "created_by": companies.created_by,
#         #     "created_at": companies.created_at.isoformat() if companies.created_at else None,
#         #     "updated_by": companies.updated_by,
#         #     "updated_at": companies.updated_at.isoformat() if companies.updated_at else None,
#         #     "is_deleted": companies.is_deleted,
#         #     "deleted_by": companies.deleted_by,
#         #     "deleted_at": companies.deleted_at.isoformat() if companies.deleted_at else None,
#         #     "sector_name": companies.sector.sector_name if companies.sector else None
#         #     }
#         return product

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][GET_ALL_product] Error in Fetch product.: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False
    
    
# # async def update_product_db(
# #         product_id ,
# #         product_name,
# #         product_price,
# #         product_description,
# #         user_id : int,
# #         current_product_name: str,
# #         session: AsyncSession,
# #         background_tasks : BackgroundTasks,
# # ):
# #     try:
# #         data = {}
# #         if product_name:
# #             data["product_name"] = product_name
# #         if product_price:
# #             data["product_price"] = product_price
# #         if product_description:
# #             data["product_description"] = product_description
# #         data["updated_by"] = user_id
# #         data["updated_at"] = func.now()

# #         stmt = update(Products).where(Products.product_id==product_id).values(**data)
# #         result = await session.execute(stmt)
# #         await session.commit()
# #         update_result = result.rowcount
# #         if update_result==1:
# #             log_entry_result = await log_entry(
# #                 background_tasks=background_tasks,
# #                 session=session,
# #                 log_name="product Updated",
# #                 log_description=f"product Updated by user_id {user_id}",
# #                 previous_value=current_product_name,
# #                 updated_value=data,
# #                 changed_by=user_id
# #                 )
# #             if log_entry_result:
# #                 return True
# #             return True
# #         else:
# #             return False

# #     except Exception as e:
# #         log_async(
# #             background_tasks,
# #             f"[DB][UPDATE_product] Error in Updating product {current_product_name}: {str(e)}",
# #             "error",
# #             always_sync=True
# #         )
# #         # raise HTTPException(
# #         #     detail=f"Database error Error Creating product: {e}")

# #         return False
    

# async def cancel_buy_product_db(   
#         buy_product_id:int,
#         current_product_name:str,
#         user_id : int,
#         session: AsyncSession,
#         background_tasks : BackgroundTasks, 
# ):
#     try:
#         data = {}
#         data["is_canceled"] = True
#         data["deleted_by"] = user_id
#         data["deleted_at"] = func.now()
#         stmt = update(BuyProducts).where(BuyProducts.buy_product_id==buy_product_id).values(**data)
#         result = await session.execute(stmt)
#         await session.commit()
#         product_result = result.rowcount
#         if product_result != 1:
#             return False
#         if product_result == 1:
#             log_entry_result = await log_entry(
#                 session=session,
#                 background_tasks=background_tasks,
#                 log_name="product canceled",
#                 log_description=f"product with buy_product id {buy_product_id} deleted by user_id {user_id}",
#                 previous_value="is_canceled=0",
#                 updated_value="is_canceled=1",
#                 changed_by=user_id
#                 )
#             if log_entry_result:
#                 return True
#             return True

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][DELETE_product] Error in Delete canceled {current_product_name}: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         return False