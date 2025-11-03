# '''
# All user related CRUD operations
# '''

from typing import Optional
from fastapi import FastAPI, Depends, BackgroundTasks, File, Form, UploadFile, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.cart_repository import check_cart_name_db
from app.microservices.common_function import get_current_role, get_current_user

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session 
from app.db.models.db_base import BuyProducts, Categary, OrderAlert, Products, SubCategary, Users
from app.microservices.order_alert.order_alert_service import get_all_order_admin_service, get_all_order_service, get_order_id_service
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background 
from config.config import settings

global_prefix = settings.global_prefix
app = FastAPI()
router_v1 = APIRouter(prefix=f"/{global_prefix}/order_alert")

from fastapi.middleware.cors import CORSMiddleware


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     # allow_credentials=True,
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# origins = [
#     "https://75953f4650ae4bdeb8a4dba92b252976-1fc1aa975dda492589bb75afa.fly.dev",
#     # Add "http://localhost:3000" or others if needed for dev
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router_v1.post("/add/{product_id}")
async def add_cart_handler(
    # data : Createcart,
    product_id: int,
    background_tasks : BackgroundTasks,
    session : AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),
    # user = Users(user_id=1),

):
    try:

        user_id = user.user_id
        
        result = await add_cart_service(
            product_id = product_id,
            user_id=user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"]==1:
            return JSONResponse(content=result,status_code=status.HTTP_201_CREATED)
        
        else:
            raise HTTPException(detail={
                "status":0,
                "message":"Unable to create cart"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][CREATE_cart] Error: Failed to create cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=" Failed to create cart")
        

@router_v1.get("/")
async def get_all_order_handler(
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_all_order_service(
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,      
                "data": result
            })
        
        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":[]
            })
        
        else:
            return JSONResponse(content={
                "status":1,
                "data": None
            })

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[order][GET_ALL_cart] Error: Failed to Fetch all order. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all cart.")


@router_v1.get("/all-order")
async def get_all_order_admin_handler(
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        result = await get_all_order_admin_service(
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,      
                "data": result
            })
        
        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":[]
            })
        
        else:
            return JSONResponse(content={
                "status":1,
                "data": None
            })

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[order][GET_ALL_cart] Error: Failed to Fetch all order. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all cart.") 

@router_v1.get("/{order_id}")
async def get_cart_handler(
    order_id : int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        result = await get_order_id_service(
            order_id=order_id,
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
                detail="Category not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch cart.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][GET_ALL_cart] Error: Failed to Fetch cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch cart.")
    



@router_v1.get("/details/{order_id}")
async def get_order_details(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Fetch one order (from order_alert) and all its buy products (with product, category, sub-category)
    """
    try:
        # First fetch the order alert row
        q_order = await session.execute(
            select(OrderAlert).where(OrderAlert.order_alert_id == order_id)
        )
        order_alert = q_order.scalars().first()

        if not order_alert:
            raise HTTPException(status_code=404, detail="Order not found")

        # Fetch all buy products for this order_id with product/category info
        q_products = await session.execute(
            select(BuyProducts, Products, Categary, SubCategary)
            .join(Products, Products.product_id == BuyProducts.product_id)
            .join(Categary, Categary.category_id == BuyProducts.category_id, isouter=True)
            .join(SubCategary, SubCategary.sub_category_id == BuyProducts.sub_category_id, isouter=True)
            .where(BuyProducts.order_id == order_alert.order_id)   # ✅ FIX HERE
        )
        buy_products = q_products.all()

        # Build response
        response = {
            "order_alert_id": order_alert.order_alert_id,
            "order_id": order_alert.order_id,
            "delivery_status": order_alert.delivery_status,
            "total_amount": order_alert.total_amount,
            "created_at": order_alert.created_at,
            "products": []
        }

        for bp, p, c, sc in buy_products:
            response["products"].append({
                "buy_product_id": bp.buy_product_id,
                "quantity": bp.quantity,
                "price": bp.product_price,
                "shipping_address": bp.shipping_address,
                "payment_method": bp.payment_method,
                "payment_status": bp.payment_status,
                "product": {
                    "product_id": p.product_id,
                    "product_name": p.product_name,
                    "product_price": p.product_price,
                    "product_description": p.product_description,
                    "product_image": p.product_image,
                },
                "category": {
                    "category_id": c.category_id if c else None,
                    "category_name": c.category_name if c else None,
                },
                "sub_category": {
                    "sub_category_id": sc.sub_category_id if sc else None,
                    "sub_category_name": sc.sub_category_name if sc else None,
                },
            })

        return {"status": 1, "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @router_v1.patch("/update/{cart_id}")
# async def update_cart_handler(
#     cart_id : int,
#     background_tasks: BackgroundTasks,
#     cart_name : Optional[str] = None,
#     file: Optional[UploadFile] = File(None),
#     user: Users = Depends(get_current_user),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
#         user_id = user.user_id
#         role_result = await get_current_role(
#             user_id = user_id,
#             background_tasks=background_tasks,
#             session=session,
#         )

#         file = file
#         if file is None:
#             cart_image = None

#         else:
#             cart_image = file

#         check_cart = await check_cart_service(
#             cart_id=cart_id,
#             session=session,
#             background_tasks=background_tasks,
#         )
#         current_cart_name = check_cart.cart_name

#         check_cart_name = await check_cart_name_db(
#             cart_name = cart_name,
#             session=session,
#             background_tasks=background_tasks,
#         )
#         if check_cart_name:
#             raise HTTPException(
#                 detail="cart Already Used",
#                 status_code=status.HTTP_409_CONFLICT
#             )
        
    #     result = await update_cart_service(
    #         cart_id=cart_id,
    #         cart_name=cart_name,
    #         cart_image= cart_image,
    #         user_id = user.user_id,
    #         current_cart_name=current_cart_name,
    #         session=session,
    #         background_tasks=background_tasks,
    #     )

    #     if result:
    #         return JSONResponse(content={
    #             "status":1,
    #             "data":result
    #         })
        
    #     else:
    #         raise HTTPException(status_code=500, detail="Failed to Update cart.")

    # except HTTPException as http_exc:
    #     raise http_exc

    # except Exception as e:
    #     log_async(
    #         background_tasks=background_tasks,
    #         message=f"[cart][UPDATE_cart] Error: Failed to Update cart. Exception: {e}",
    #         level="error",
    #         always_sync=True
    #     )
    #     raise HTTPException(status_code=500, detail="Failed to Update cart.")
    

@router_v1.put("/remove/{cart_id}")
async def remove_cart_handler(
    cart_id : int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:

        check_cart = await check_cart_service(
            cart_id=cart_id,
            session=session,
            background_tasks=background_tasks,
        )

        # is_deleted = check_cart.is_deleted
        # if is_deleted == True or is_deleted==1:
        #     raise HTTPException(
        #         detail="cart Already deleted",
        #         status_code=status.HTTP_404_NOT_FOUND
        #     )

        result = await remove_cart_service(
            user_id= user.user_id,
            cart_id=cart_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "message":"cart Delete Successfully"
            })
        
        else:
            raise HTTPException(
                detail="Unable to Delete cart",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[cart][UPDATE_cart] Error: Failed to Update cart. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update cart.")

app.include_router(router_v1)

# if __name__=="__main__":
#     uvicorn.run("app.microservices.order_alert.order_alert_routes:app", host="0.0.0.0", port=9024,reload=True)


