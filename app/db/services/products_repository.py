import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.db_base import Products, Roles, UserRoles, Users 
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


# async def create_product_db(
#         product_name,
#         product_price,
#         product_image,
#         product_description,
#         sub_category_id,
#         user_id,
#         session: AsyncSession,
#         background_tasks : BackgroundTasks,
# ):
#     try:
#         new_product = Products(
#             product_name = product_name,
#             product_price = product_price,
#             product_description = product_description,
#             product_image = product_image,
#             sub_category_id = sub_category_id,
#             created_by = user_id
#             )
#         session.add(new_product)
#         await session.commit()
#         result = await session.refresh(new_product)
#         if new_product.product_id:
#             new_product_id = new_product.product_id
#             log_entry_result = await log_entry(
#                 background_tasks=background_tasks,
#                 session=session,
#                 log_name=f"product: {product_name} created",
#                 log_description=f"product {product_name} Created by user_id {user_id}",
#                 previous_value=None,
#                 updated_value=product_name,
#                 changed_by=user_id)
#             if log_entry_result:
#                 return True
#             return True
#         else:
#             return False

#     except Exception as e:
#         log_async(
#             background_tasks,
#             f"[DB][CREATE_product] Error Creating product {product_name}: {str(e)}",
#             "error",
#             always_sync=True
#         )
#         # raise HTTPException(
#         #     detail=f"Database error Error Creating product: {e}")

#         return False


async def create_product_db(
    product_name,
    product_price,
    product_full_price,
    product_image,
    product_description,
    sub_category_id,
    stock,
    weight,
    length,
    width,
    height,
    origin_location,
    user_id,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        new_product = Products(
            product_name=product_name,
            product_price=product_price,
            product_full_price=product_full_price,
            product_description=product_description,
            product_image=product_image,
            sub_category_id=sub_category_id,
            stock=stock,
            weight=weight,
            length=length,
            width=width,
            height=height,
            origin_location=origin_location,
            created_by=user_id,
        )

        # auto calculate volumetric weight
        new_product.calculate_volumetric_weight()

        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)

        if new_product.product_id:
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CREATE_product] Error creating product {product_name}: {str(e)}",
            "error",
            always_sync=True,
        )
        return False

    

async def check_product_name_db(
        product_name: str,
        session: AsyncSession,
        background_tasks :BackgroundTasks,
):
    try:
        stmt = select(Products).where(Products.product_name == product_name)
        result = await session.execute(stmt)
        search_result = result.scalars().first()
        return search_result

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][CHECK_product_NAME_DB] Error Checking product Name: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_all_product_db(
    session: AsyncSession,
    background_tasks: BackgroundTasks,
    page: int,
    page_size: int,
):
    try:
        # 1️⃣ Count total items
        total_stmt = select(func.count(Products.product_id))
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar() or 0

        if total_count == 0:
            return [], 0

        # 2️⃣ Apply pagination
        offset = (page - 1) * page_size
        stmt = select(Products).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        products = result.scalars().all()

        # 3️⃣ Convert to dicts
        data = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_price": row.product_price,
                "product_full_price": row.product_full_price,
                "product_image": row.product_image,
                "product_description": row.product_description,
                "stock":row.stock,
                "sub_category_id": row.sub_category_id,
                "created_by": row.created_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_by": row.updated_by,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "is_deleted": row.is_deleted,
                "deleted_by": row.deleted_by,
                "deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
            }
            for row in products
        ]

        return data, total_count

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_product] Error in Fetch All product: {str(e)}",
            "error",
            always_sync=True
        )
        return [], 0
    


async def get_product_db(
        product_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        # stmt = select(product).where(product.product_id==product_id)
        stmt = select(Products).where(Products.product_id==product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()

        if not product:
            return None

        # Clean images field if it exists
        

        # data = {
        #     "product_id": product.product_id,
        #     "product_name": product.product_name,
        #     "sector_id": product.sector_id,
        #     "created_by": product.created_by,
        #     "created_at": product.created_at.isoformat() if product.created_at else None,
        #     "updated_by": product.updated_by,
        #     "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        #     "is_deleted": product.is_deleted,
        #     "deleted_by": product.deleted_by,
        #     "deleted_at": product.deleted_at.isoformat() if product.deleted_at else None,
        #     "sector_name": product.sector.sector_name if product.sector else None,
        #     "images": images,  # cleaned JSON array
        # }

        # return data

        return product

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_ALL_product] Error in Fetch product.: {str(e)}",
            "error",
            always_sync=True
        )
        return False
    

async def get_product_sub_category_db(
    sub_category_id: int,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
    page: int,
    page_size: int,
):
    try:
        # 1️⃣ Count total
        total_stmt = select(func.count(Products.product_id)).where(
            (Products.sub_category_id == sub_category_id) & (Products.is_deleted == False)
        )
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar() or 0

        if total_count == 0:
            return [], 0

        # 2️⃣ Apply pagination
        offset = (page - 1) * page_size
        stmt = (
            select(Products)
            .where((Products.sub_category_id == sub_category_id) & (Products.is_deleted == False))
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        products = result.scalars().all()

        return products, total_count

    except Exception as e:
        log_async(
            background_tasks,
            f"[DB][GET_product_sub_category] Error in Fetch product: {str(e)}",
            "error",
            always_sync=True,
        )
        return [], 0
    
    

async def update_product_db(
    product_id: int,
    product_name: Optional[str],
    product_price: Optional[int],
    product_full_price: Optional[int],
    product_description: Optional[str],
    sub_category_id: Optional[int],
    stock: Optional[int],
    product_images: Optional[List[str]],  # ✅ Now expects list of URLs
    weight: Optional[float],
    length: Optional[float],
    width: Optional[float],
    height: Optional[float],
    origin_location: Optional[str],
    current_product_name: str,
    user_id: int,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        data = {}

        # --- Only add changed fields ---
        if product_name:
            data["product_name"] = product_name
        if product_price is not None:
            data["product_price"] = product_price
        if product_full_price is not None:
            data["product_full_price"] = product_full_price
        if product_description:
            data["product_description"] = product_description
        if sub_category_id:
            data["sub_category_id"] = sub_category_id
        if stock is not None:
            data["stock"] = stock
        if weight is not None:
            data["weight"] = weight
        if length is not None:
            data["length"] = length
        if width is not None:
            data["width"] = width
        if height is not None:
            data["height"] = height
        if origin_location:
            data["origin_location"] = origin_location

        # --- ✅ Handle product images (already processed URLs) ---
        if product_images is not None:
            data["product_image"] = product_images

        data["updated_by"] = user_id
        data["updated_at"] = func.now()

        stmt = (
            update(Products)
            .where(Products.product_id == product_id)
            .values(**data)
        )
        result = await session.execute(stmt)
        await session.commit()

        # --- Log successful update ---
        if result.rowcount == 1:
            # log_entry(
            #     background_tasks=background_tasks,
            #     session=session,
            #     log_name="Product Updated",
            #     log_description=f"Product updated by user_id {user_id}",
            #     previous_value=current_product_name,
            #     updated_value=data,
            #     changed_by=user_id,
            # )
            return True
        else:
            return False

    except Exception as e:
        log_async(
            background_tasks,
              f"[DB][UPDATE_product] Error updating product {current_product_name}: {e}",
            "error",
            always_sync=True,
        )
        return False
    

async def delete_product_db(   
        product_id:int,
        current_product_name:str,
        user_id : int,
        session: AsyncSession,
        background_tasks : BackgroundTasks, 
):
    try:
        data = {}
        data["is_deleted"] = True
        data["deleted_by"] = user_id
        data["deleted_at"] = func.now()
        stmt = update(Products).where(Products.product_id==product_id).values(**data)
        result = await session.execute(stmt)
        await session.commit()
        product_result = result.rowcount
        if product_result != 1:
            return False
        if product_result == 1:
            log_entry_result = await log_entry(
                session=session,
                background_tasks=background_tasks,
                log_name="product Deleted",
                log_description=f"product with product id {product_id} deleted by user_id {user_id}",
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
            f"[DB][DELETE_product] Error in Delete product {current_product_name}: {str(e)}",
            "error",
            always_sync=True
        )
        return False