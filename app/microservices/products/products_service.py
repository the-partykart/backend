import json
from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.products_repository import create_product_db, delete_product_db, get_all_product_db, get_product_db, get_product_sub_category_db, update_product_db
from app.microservices.common_function import object_to_dict, upload_image
from app.utility.logging_utils import log_async 

from datetime import datetime   

# Validation
async def check_product_service(
        product_id: int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_product_db(
            product_id= product_id,
            session=session,
            background_tasks=background_tasks,
        )

        if not result or result is None:
            raise HTTPException(detail="product Not Found", status_code= status.HTTP_404_NOT_FOUND)
        elif result.product_id and result.is_deleted==True:
            raise HTTPException(detail="product Not Found (product Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        else:
            return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create product: {e}"
        )


# async def create_product_service(
#     product_name,
#     product_images,   # list of UploadFile
#     product_price,
#     product_description,
#     sub_category_id,
#     user_id,
#     session: AsyncSession,
#     background_tasks: BackgroundTasks,
# ):
#     try:
#         uploaded_urls = []
#         if product_images:
#             for file in product_images:
#                 upload_result = await upload_image(file=file, background_tasks=background_tasks)
#                 if upload_result:
#                     uploaded_urls.append(upload_result)

#         result = await create_product_db(
#             product_name=product_name,
#             product_image=uploaded_urls if uploaded_urls else None,  # save list
#             product_price=product_price,
#             product_description=product_description,
#             sub_category_id=sub_category_id,
#             user_id=user_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return {
#                 "status":1,
#                 "message":"product create successfully"
#                 }
        
#         else:
#             return False
        
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         await log_async(
#             background_tasks=background_tasks,
#             message=f"[product_SERVICE][CREATE_product_SERVICE] Error in create product Service: Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(
#             status_code=404,
#             detail=f"Error in Create product: {e}"
#         )


async def create_product_service(
    product_name,
    product_images,
    product_price,
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
        uploaded_urls = []
        if product_images:
            for file in product_images:
                upload_result = await upload_image(file=file, background_tasks=background_tasks)
                if upload_result:
                    uploaded_urls.append(upload_result)

        result = await create_product_db(
            product_name=product_name,
            product_image=uploaded_urls if uploaded_urls else None,
            product_price=product_price,
            product_description=product_description,
            sub_category_id=sub_category_id,
            weight=weight,
            stock=stock,
            length=length,
            width=width,
            height=height,
            origin_location=origin_location,
            user_id=user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return {"status": 1, "message": "Product created successfully"}
        else:
            return {"status": 0, "message": "Failed to create product"}

    except Exception as e:
        await log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][CREATE_product_SERVICE] Error: {e}",
            level="error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail=f"Error creating product: {e}")


async def get_all_product_service(
    session: AsyncSession,
    background_tasks: BackgroundTasks,
    page: int,
    page_size: int,
):
    try:
        result, total_count = await get_all_product_db(
            session=session,
            background_tasks=background_tasks,
            page=page,
            page_size=page_size,
        )

        if total_count == 0:
            return None, 0

        return result, total_count

    except Exception as e:
        await log_async(
            background_tasks=background_tasks,
            message=f"[product][GET_ALL_product] Service Error: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch product data.")



async def get_product_service(
        product_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_product_db(
            product_id=product_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result:
            # data = {
            #     col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
            #     for col in result.__table__.columns
            # }
            # return data

            # images = None
            # if result.product_image:
            #     try:
            #         # Remove unwanted newlines and spaces
            #         clean_str = result.product_image.replace("\n", "").strip()
            #         images = json.loads(clean_str)
            #     except Exception as e:
            #         images = []  

            data = {
            "product_id": result.product_id,
            "product_name": result.product_name,
            "product_price": result.product_price,
            "product_image":result.product_image,
            "product_description": result.product_description,
            # "stock": result.stock,
            "sub_category_id": result.sub_category_id,
            "created_by": result.created_by,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_by": result.updated_by,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            "is_deleted": result.is_deleted,
            "deleted_by": result.deleted_by,
            "deleted_at": result.deleted_at.isoformat() if result.deleted_at else None,
            }

            if result.stock is None:
                return data

            if result.stock <= 5:
                data["stock"] = result.stock

            return data
        
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[product][GET_product] Error: Failed Logic to Fetch product.",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch product.")


    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][GET_ALL_product] Error: Failed to Fetch product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to Fetch product.{e}")


async def update_product_service(
        product_id,
        product_name,
        product_image,
        product_price,
        product_description,
        sub_category_id,
        user_id,
        current_product_name,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await update_product_db(
            product_id = product_id,
            product_name=product_name,
            product_price=product_price,
            product_image=product_image,
            product_description=product_description,
            sub_category_id = sub_category_id,
            current_product_name=current_product_name,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return{"status":1,"message":"product Update successfully"}
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][CREATE_product_SERVICE] Error in create product Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create product: {e}"
        )
    
async def delete_product_service(
    product_id,
    user_id,
    current_product_name,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await delete_product_db(
            product_id = product_id,
            current_product_name=current_product_name,
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
        await log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][DELETE_product_SERVICE] Error in Delete product Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete product: {e}"
        )
    

async def get_product_category_service(
    sub_category_id: int,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
    page: int,
    page_size: int,
):
    try:
        result, total_count = await get_product_sub_category_db(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
            page=page,
            page_size=page_size,
        )

        if total_count == 0:
            return [], 0

        data = [await object_to_dict(r) for r in result]
        return data, total_count

    except Exception as e:
        await log_async(
            background_tasks,
            f"[Service][GET_product_category] Error: {e}",
            "error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch product by subcategory.")
