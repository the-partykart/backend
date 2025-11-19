# '''
# All product related CRUD operations
# '''

from typing import List, Optional
from fastapi import FastAPI, Depends, BackgroundTasks, File, Form, Query, UploadFile, status
from fastapi import HTTPException, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.category_repository import get_category_db, get_sub_category_db
from app.db.services.products_repository import check_product_name_db
from app.microservices.common_function import get_current_role, get_current_user, object_to_dict, upload_image
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.models.db_base import Courses, DashBoardImage, Products, Users
from app.microservices.products.products_schema import CourseCreate, CourseResponse, CreateProduct, Updateproduct
from app.microservices.products.products_service import check_product_service, create_product_service, delete_product_service, get_all_product_service, get_product_category_service, get_product_service, update_product_service
# from app.microservices.sectors.sectors_service import check_sector_service
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background, log
from config.config import settings

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

prefix = settings.global_prefix

app = FastAPI()
router_v1 = APIRouter(prefix=f"/{prefix}/products")

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Configuration       
cloudinary.config( 
    cloud_name = settings.cloud_name, 
    api_key = settings.api_key, 
    api_secret = settings.api_secret, # Click 'View API Keys' above to copy your API secret
    secure=True
)


@router_v1.post("/create")
async def create_product_handler(
    background_tasks: BackgroundTasks,
    product_name: str = Form(...),
    product_price: int = Form(...),
    product_full_price: Optional[int] = Form(None),
    product_description: Optional[str] = Form("No information available for this product"),
    sub_category_id: Optional[int] = Form(None),
    stock: Optional[int] = Form(None),
    files: List[UploadFile] = File(None),  # <-- multiple files
    # new optional shipping fields
    weight: Optional[float] = Form(None),
    length: Optional[float] = Form(None),
    width: Optional[float] = Form(None),
    height: Optional[float] = Form(None),
    origin_location: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id=user_id,
            background_tasks=background_tasks,
            session=session,
        )

        # image handling
        product_images = files if files else None

        # check for duplicate product
        check_product_name = await check_product_name_db(
            product_name=product_name,
            session=session,
            background_tasks=background_tasks,
        )
        if check_product_name:
            raise HTTPException(
                detail="Product Already Created",
                status_code=status.HTTP_409_CONFLICT
            )

        # validate subcategory if provided
        if sub_category_id:
            check_sub_category_id = await get_sub_category_db(
                sub_category_id=sub_category_id,
                session=session,
                background_tasks=background_tasks,
            )
            if not check_sub_category_id or check_sub_category_id.is_deleted == 1:
                sub_category_id = None

        # pass to service layer
        result = await create_product_service(
            product_name=product_name,
            product_price=product_price,
            product_full_price = product_full_price,
            product_images=product_images,
            product_description=product_description,
            sub_category_id=sub_category_id,
            weight=weight,
            length=length,
            stock=stock,
            width=width,
            height=height,
            origin_location=origin_location,
            user_id=user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"] == 1:
            return JSONResponse(content=result, status_code=status.HTTP_201_CREATED)
        else:
            raise HTTPException(
                detail={"status": 0, "message": "Unable to create product"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][CREATE_product] Error: Failed to create product. Exception: {e}",
            level="error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to create product")


@router_v1.get("/all")
async def get_all_product_handler(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Paginated product list
    """
    try:
        result, total_count = await get_all_product_service(
            session=session,
            background_tasks=background_tasks,
            page=page,
            page_size=page_size,
        )

        if result is None or len(result) == 0:
            return JSONResponse(content={
                "status": 1,
                "data": [],
                "total_items": 0,
                "total_pages": 0,
                "page_no": page,
                "page_size": page_size
            })

        total_pages = (total_count + page_size - 1) // page_size  # ceil division

        return JSONResponse(content={
            "status": 1,
            "data": result,
            "total_items": total_count,
            "total_pages": total_pages,
            "page_no": page,
            "page_size": page_size
        })

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][GET_ALL_product] Error: Failed to Fetch all product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all product.")


@router_v1.get("/search")
async def search_products(
    q: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search products by product_name only.
    Returns product_id and product_name.
    """
    try:

        query = (
            select(Products.product_id, Products.product_name)
            .where(
                Products.product_name.ilike(f"%{q}%"),
                Products.is_deleted == False
            )
        )

        result = await session.execute(query)
        products = result.all()  # Since we selected columns, we use .all()

        return [
            {"product_id": p.product_id, "product_name": p.product_name}
            for p in products
        ]

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log.error(f"[dashboard_image][DELETE] Error: {str(e)}")   
        raise HTTPException(status_code=500, detail="Failed to search Product")


@router_v1.get("/admin/search")
async def search_products(
    q: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search products by product_name only.
    Returns full product details.
    """
    try:
        query = (
            select(Products)
            .where(
                Products.product_name.ilike(f"%{q}%"),
                Products.is_deleted == False
            )
        )

        result = await session.execute(query)
        rows = result.scalars().all()  # fetch full model rows

        response = []
        for row in rows:
            response.append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_price": row.product_price,
                "product_full_price": row.product_full_price,
                "product_image": row.product_image,
                "product_description": row.product_description,
                "stock": row.stock,
                "sub_category_id": row.sub_category_id,
                "created_by": row.created_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_by": row.updated_by,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "is_deleted": row.is_deleted,
                "deleted_by": row.deleted_by,
                "deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
            })

        return response

    except HTTPException:
        raise

    except Exception as e:
        log.error(f"[adminsearch] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Product")



@router_v1.get("/{product_id}")
async def get_product_handler(
    product_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_product_service(
            product_id=product_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })

        if result is None:
            raise HTTPException(
                detail="Compnay not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch product.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][GET_ALL_product] Error: Failed to Fetch product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch product.")
    



@router_v1.get("/details/{product_id}")
async def get_product_detail_handler(
    product_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        # Fetch product by ID
        stmt = select(Products).where(Products.product_id == product_id, Products.is_deleted == 0)
        result = await session.execute(stmt)
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Parse product images (if stored as JSON string)


        # product_images = []
        # if product.product_image:
        #     try:
        #         clean_str = product.product_image.replace("\n", "").strip()
        #         product_images = json.loads(clean_str)
        #     except Exception:
        #         product_images = [product.product_image] if isinstance(product.product_image, str) else []

        # Prepare response data
        data = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_price": product.product_price,
            "product_full_price":product.product_full_price,
            "product_description": product.product_description,
            "sub_category_id": product.sub_category_id,
            "stock": product.stock,
            "weight": product.weight,
            "length": product.length,
            "width": product.width,
            "height": product.height,
            "origin_location": product.origin_location,
            "product_images": product.product_image,
            "created_by": product.created_by,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_by": product.updated_by,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }

        # return JSONResponse(content={"status": 1, "data": data}, status_code=200)
        json_data = jsonable_encoder({"status": 1, "data": data})
        return JSONResponse(content=json_data, status_code=200)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][DETAIL_product] Error fetching product {product_id}: {e}",
            level="error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch product details")



@router_v1.get("/sub_category/{sub_category_id}")
async def get_product_sub_category_handler(
    sub_category_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    try:
        result, total_count = await get_product_category_service(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
            page=page,
            page_size=page_size,
        )

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

        return JSONResponse(
            content={
                "status": 1,
                "data": result or [],
                "total_items": total_count,
                "total_pages": total_pages,
                "page_no": page,
                "page_size": page_size,
            },
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks,
            f"[product][GET_product_sub_category] Error: Failed to Fetch products. Exception: {e}",
            "error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch product.")





@router_v1.patch("/update/{product_id}")
async def update_product_handler(
    product_id: int,
    background_tasks: BackgroundTasks,
    product_name: Optional[str] = Form(None),
    product_price: Optional[int] = Form(None),
    product_full_price : Optional[int] = Form(None),
    product_description: Optional[str] = Form(None),
    sub_category_id: Optional[int] = Form(None),
    stock: Optional[int] = Form(None),
    files: List[UploadFile] = File(None),  # new uploaded images
    existing_images: Optional[str] = Form("[]"),  # JSON string of kept old images
    weight: Optional[float] = Form(None),
    length: Optional[float] = Form(None),
    width: Optional[float] = Form(None),
    height: Optional[float] = Form(None),
    origin_location: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    import json

    try:
        user_id = user.user_id

        # --- Validate role ---
        await get_current_role(
            user_id=user_id,
            background_tasks=background_tasks,
            session=session,
        )

        # --- Check product existence ---
        product_data = await check_product_service(
            product_id=product_id,
            session=session,
            background_tasks=background_tasks,
        )
        if not product_data:
            raise HTTPException(status_code=404, detail="Product not found")

        current_product_name = product_data.product_name

        # --- Check for duplicate name ---
        if product_name and product_name != current_product_name:
            if await check_product_name_db(
                product_name=product_name,
                session=session,
                background_tasks=background_tasks,
            ):
                raise HTTPException(status_code=409, detail="Product name already exists")

        # --- Validate subcategory ---
        if sub_category_id:
            check_sub_category_id = await get_sub_category_db(
                sub_category_id=sub_category_id,
                session=session,
                background_tasks=background_tasks,
            )
            if not check_sub_category_id or check_sub_category_id.is_deleted == 1:
                sub_category_id = None

        # --- Parse existing images (from frontend) ---
        try:
            if isinstance(existing_images, str):
                existing_images_list = json.loads(existing_images)
            else:
                existing_images_list = existing_images
        except Exception:
            existing_images_list = []
        
        if not isinstance(existing_images_list, list):
            existing_images_list = []

        # --- Handle new image uploads ---
        new_image_urls = []
        if files:
            for file in files:
                upload_result = await upload_image(file=file, background_tasks=background_tasks)
                if upload_result:
                    new_image_urls.append(upload_result)

        # ✅ Combine existing + new uploaded
        updated_images = existing_images_list + new_image_urls

        # --- Call service layer ---
        result = await update_product_service(
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            product_full_price=product_full_price,
            product_description=product_description,
            sub_category_id=sub_category_id,
            stock=stock,
            product_images=updated_images,  # ✅ updated list
            weight=weight,
            length=length,
            width=width,
            height=height,
            origin_location=origin_location,
            user_id=user_id,
            current_product_name=current_product_name,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"] == 1:
            return JSONResponse(content=result, status_code=200)
        else:
            raise HTTPException(status_code=500, detail="Failed to update product")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][UPDATE_product] Error updating product {product_id}: {e}",
            level="error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to update product")





@router_v1.put("/delete/{product_id}")
async def delete_product_handler(
    product_id : int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    # user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        check_product = await check_product_service(
            product_id=product_id,
            session=session,
            background_tasks=background_tasks,
        )

        current_product_name = check_product.product_name

        result = await delete_product_service(
            current_product_name=current_product_name,
            user_id= user.user_id,
            product_id=product_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "message":"product Delete Successfully"
            })
        
        else:
            raise HTTPException(
                detail="Unable to Delete product",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][UPDATE_product] Error: Failed to Update product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update product.")





@router_v1.post("/dashboard-image/")
async def create_dashboard_image_handler(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dashboard_image_order: int = Form(...),
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    try:
        user_id = user.user_id

        # Role check (optional, if required)
        await get_current_role(
            user_id=user_id,
            background_tasks=background_tasks,
            session=session,
        )

        # Call your file upload function
        dashboard_image_link = await upload_image(file=file, background_tasks=background_tasks)   #TODO uncomment this and refactor upload_file()
        # dashboard_image_link = "https://pixnio.com/food-and-drink/fried-fish-french-fries-from-the-fishette-on-harbor"

        new_image = DashBoardImage(
            dashboard_image_link=dashboard_image_link,
            dashboard_image_order=dashboard_image_order,
            created_by=user_id,
            created_at=datetime.utcnow()
        )

        session.add(new_image)
        await session.commit()
        await session.refresh(new_image)

        return JSONResponse(
            content={
                "status": 1,
                "message": "Dashboard image uploaded successfully",
                "data": {
                    "dashboard_image_id": new_image.dashboard_image_id,
                    "dashboard_image_link": new_image.dashboard_image_link,
                    "dashboard_image_order": new_image.dashboard_image_order,
                },
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[dashboard_image][CREATE] Error: {str(e)}",
            level="error",
            always_sync=True,
        )
        raise HTTPException(status_code=500, detail="Failed to upload dashboard image")

# -------------------------------
# Fetch All Dashboard Images (Ordered)
# -------------------------------
@router_v1.get("/dashboard-image/")
async def get_all_dashboard_images_handler(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        stmt = (
            select(DashBoardImage)
            .where(DashBoardImage.is_deleted == False)
            .order_by(DashBoardImage.dashboard_image_order.asc())
        )
        result = await session.execute(stmt)
        images = result.scalars().all()

        if images is None:
            return JSONResponse(content={
            "status": 1,
            "data": [
                None
            ]
        })

        return JSONResponse(content={
            "status": 1,
            "data": [
                {
                    "dashboard_image_id": img.dashboard_image_id,
                    "dashboard_image_link": img.dashboard_image_link,
                    "dashboard_image_order": img.dashboard_image_order,
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                }
                for img in images
            ]
        })

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[dashboard_image][FETCH_ALL] Error: {str(e)}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard images")


# -------------------------------
# Delete Dashboard Image (Soft Delete)
# -------------------------------
@router_v1.put("/delete/dashboard-image/{dashboard_image_id}")
async def delete_dashboard_image_handler(
    dashboard_image_id: int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id

        # Role check (optional)
        await get_current_role(
            user_id=user_id,
            background_tasks=background_tasks,
            session=session,
        )

        stmt = select(DashBoardImage).where(DashBoardImage.dashboard_image_id == dashboard_image_id)
        result = await session.execute(stmt)
        dashboard_image = result.scalar_one_or_none()

        if not dashboard_image or dashboard_image.is_deleted:
            raise HTTPException(status_code=404, detail="Dashboard image not found")

        dashboard_image.is_deleted = True
        dashboard_image.deleted_by = user_id
        dashboard_image.deleted_at = datetime.utcnow()

        session.add(dashboard_image)
        await session.commit()

        return JSONResponse(content={
            "status": 1,
            "message": "Dashboard image deleted successfully"
        })

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[dashboard_image][DELETE] Error: {str(e)}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete dashboard image")


# ## ------------------------ courses



# ✅ Upload / Create a course
@router_v1.post("/courses/create", response_model=CourseResponse, summary="Upload a new course")
async def create_course(
    data: CourseCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    new_course = Courses(
        course_name=data.course_name,
        course_link=data.course_link,
        created_by=user.user_id if user else None,
        created_at=datetime.utcnow(),
        is_deleted=False,
    )

    session.add(new_course)
    await session.commit()
    await session.refresh(new_course)

    return new_course

# Fetch all courses
@router_v1.get("/courses/list", summary="Fetch all courses")
async def get_all_courses(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Courses).where(Courses.is_deleted == False))
    courses = result.scalars().all()
    return {"status": 1, "data": courses}


# ✅ Delete course (soft delete)
@router_v1.delete("/courses/{course_id}", summary="Delete a course")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),  # whoever is logged in
):
    query = select(Courses).where(Courses.course_id == course_id, Courses.is_deleted == False)
    result = await session.execute(query)
    course = result.scalars().first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or already deleted",
        )

    # soft delete
    stmt = (
        update(Courses)
        .where(Courses.course_id == course_id)
        .values(
            is_deleted=True,
            canceled_by=user.user_id if user else None,
            canceled_at=datetime.utcnow(),
        )
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": 1, "message": f"Course {course_id} deleted successfully"}




app.include_router(router_v1)

if __name__=="__main__":
    uvicorn.run("app.microservices.products.products_routes:app", host="0.0.0.0", port=9004,reload=True)


