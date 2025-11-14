# '''
# All product related CRUD operations
# '''

from typing import List, Optional
from fastapi import FastAPI, Depends, BackgroundTasks, Query, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.category_repository import get_category_db
from app.db.services.offers_repository import get_offer_db
from app.db.services.order_alert_repository import new_order_db
from app.db.services.products_repository import check_product_name_db, get_product_db
from app.db.services.promocodes_repository import get_promocode_db
from app.microservices.buyed_product.buyed_product_schema import CartProductData, CartProductOfferData, ProductCategoryList, ProductCategoryList
from app.microservices.buyed_product.buyed_product_service import buy_product_service, generate_order_id, get_all_buy_product_service, get_buy_product_service, get_price_buy_product_service
from app.microservices.common_function import get_current_role, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.models.db_base import OrderItem, Users
from app.microservices.offers.offers_service import get_offer_service
from app.microservices.order_place.order_place_schema import OrderCreate
from app.microservices.order_place.order_place_service import create_order
from app.microservices.products.products_schema import CreateProduct, Updateproduct
from app.microservices.products.products_service import check_product_service, create_product_service, delete_product_service, get_all_product_service, get_product_service, update_product_service
# from app.microservices.sectors.sectors_service import check_sector_service
from app.microservices.promocodes.promocodes_service import get_promocode_service
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background 
from config.config import settings
from sqlalchemy.future import select
from app.db.models.db_base import Order
from sqlalchemy.orm import selectinload


prefix = settings.global_prefix

app = FastAPI()
router_v1 = APIRouter(prefix=f"/{prefix}/orders")

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# #--------------------------------------------------------------------------------------------------------------



@router_v1.post("/place-order", status_code=status.HTTP_201_CREATED)
async def place_order(
    data: OrderCreate,
    background_tasks : BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    """
    ✅ Place an order
    - Calculates total on backend
    - Creates order, order_items, and order_alert
    """
    order = await create_order(data, user_id=user.user_id, session=session,background_tasks=background_tasks)
    return {
        "message": "Order placed successfully",
        "order_id": order.order_id,
        "total": str(order.final_amount),
    }


@router_v1.get("/place-order/{order_id}")
async def get_order_details(order_id: int, session: AsyncSession = Depends(get_async_session)):
    # ✅ Preload order + items + product
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.order_id,
        "total": str(order.total_amount),
        "status": order.delivery_status,
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": str(item.price_per_unit),
                "subtotal": str(item.subtotal),
            }
            for item in order.items  # ✅ Correct relationship name
        ],
    }





@router_v1.get("/all")
async def get_all_user_orders(
    user: Users = Depends(get_current_user),  # in real app, get this from auth token
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all orders for a specific user.
    """
    user_id = user.user_id
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    orders = result.scalars().all()

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found for this user")

    return [
        {
            "order_id": order.order_id,
            "total_amount": str(order.total_amount),
            "final_amount": str(order.final_amount),
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "created_at": str(order.created_at),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price_per_unit": str(item.price_per_unit),
                    "subtotal": str(item.subtotal),
                }
                for item in order.items
            ],
        }
        for order in orders
    ]




@router_v1.get("/admin/all")
async def get_all_orders_for_admin(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
    delivery_status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    """
    Admin: Get all orders (with optional filters).
    """

    # ✅ 1. Role check (must be admin)
    user_id = user.user_id
    
    role_result = await get_current_role(
        user_id=user_id,
        background_tasks=background_tasks,
        session=session,
    )

    # ✅ 2. Build query
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
    )

    if delivery_status:
        query = query.where(Order.delivery_status == delivery_status)

    if payment_status:
        query = query.where(Order.payment_status == payment_status)

    if from_date and to_date:
        query = query.where(
            Order.created_at.between(from_date, to_date)
        )

    # ✅ 3. Execute
    result = await session.execute(query)
    orders = result.scalars().all()

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    # ✅ 4. Format response
    return [
        {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "total_amount": str(order.total_amount),
            "final_amount": str(order.final_amount),
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "created_at": str(order.created_at),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price_per_unit": str(item.price_per_unit),
                    "subtotal": str(item.subtotal),
                }
                for item in order.items
            ],
        }
        for order in orders
    ]













# #--------------------------------------------------------------------------------------------------------------


@router_v1.post("/")
async def buy_product_handler(
    data : List[ProductCategoryList],
    background_tasks : BackgroundTasks,
    session : AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),

):
    try:
        total_amount = 0

        order_id_result = await generate_order_id(user_id = user.user_id)
        order_id = order_id_result
        for item in data:
            product_id = item.product_id
            offer_id = item.offer_id
            quantity = item.quantity
            promocode_id = item.promocode_id
            shipping_address = item.shipping_address
            payment_method = item.payment_method
            payment_status = item.payment_status

            check_product_id = await get_product_db(
                product_id = product_id,
                session=session,
                background_tasks=background_tasks,
            )
            # so i want to build logic for inventry shop, so i create table product, categary, offer, so when from front end get data in list containning dict of selected product and in that dict contain product_id,category_id,offer_id but im confused what should best practice and best way to store in table in list form or one table for invidual by and one will mapp there, buy_product table contain 1 product , in categary ,offer_id , for user_id, and in other table we will map only buy_product id.?  
            if check_product_id is None or check_product_id.is_deleted == 1:
                # TODO add log
                continue
            
            product_price = check_product_id.product_price
            product_amount = product_price * quantity
            total_amount += product_amount
            sub_category_id = check_product_id.sub_category_id
            
            # check_category_id = await get_category_db(
            #     category_id = category_id,
            #     session=session,
            #     background_tasks=background_tasks,
            # )

            # if not check_category_id and check_category_id.is_deleted == 1:
            #     raise HTTPException(
            #         detail="Category unavailable",
            #         status_code=status.HTTP_404_NOT_FOUND
            #     )
            
            if offer_id:
                check_offer_id = await get_offer_db(
                offer_id = offer_id,
                session=session,
                background_tasks=background_tasks,
                )
                
                if not check_offer_id or check_offer_id.is_deleted == 1:
                    offer_id = None
                    offer_percentage = 0
                else:
                    offer_percentage = check_offer_id.offer_percentage       
            else : 
                offer_id = 0
                offer_percentage = 0

            if promocode_id:
                check_promocode_id = await get_promocode_db(
                    promocode_id=promocode_id,
                    session=session,
                    background_tasks=background_tasks
                )

                if check_promocode_id is None or check_promocode_id.is_deleted == 1:
                    promocode_id = None
                    promocode_amount = 0
                else:
                    promocode_amount = check_promocode_id.promocode_percentage
            else:
                promocode_id = 0
                promocode_amount = 0


            result = await buy_product_service(
                product_id = product_id,
                product_price = product_price,
                sub_category_id = sub_category_id,
                quantity=quantity,
                offer_id=offer_id,
                offer_percentage = offer_percentage,
                promocode_id = promocode_id,
                promocode_amount = promocode_amount,
                shipping_address = shipping_address,
                payment_method = payment_method,
                payment_status = payment_status,
                order_id = order_id,
                user_id=user.user_id,
                session=session,
                background_tasks=background_tasks,
            )

        order_alert = await new_order_db(
            order_id=order_id,
            buy_product_id=result,
            total_amount = total_amount,
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if order_alert:
            return JSONResponse(content={
                "message":"buy product successfully.",
                "order_id":order_id
            },status_code=status.HTTP_201_CREATED)
        
        else:
            raise HTTPException(detail={
                "status":0,
                "message":"Unable to proccessed buy product"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][BUY_Product] Error: Failed to create product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=" Failed to create product")
        

@router_v1.get("/")
async def get_all_buy_handler(
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    user= Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_all_buy_product_service(
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,      
                "data":result
            })
        
        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":"Empty"
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch all buyproduct.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product][GET_ALL_BUY_product] Error: Failed to Fetch all product. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all product.")
    

@router_v1.get("/{buy_product_id}")
async def get_buy_product_handler(
    buy_product_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_buy_product_service(
            buy_product_id=buy_product_id,
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
                detail="buy-product not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch buy_product_id.")

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
    
# @router_v1.patch("/{product_id}")
# async def update_product_handler(
#     product_id : int,
#     data: Updateproduct,
#     background_tasks: BackgroundTasks,
#     # user: Users = Depends(get_current_user),
#     user = Users (user_id=1),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
        
#         check_product = await check_product_service(
#             product_id=product_id,
#             session=session,
#             background_tasks=background_tasks,
#         )
#         current_product_name = check_product.product_name

#         if data.product_name:
#             check_product_name = await check_product_name_db(
#                 product_name = data.product_name,
#                 session=session,
#                 background_tasks=background_tasks,
#             )

#             if check_product_name:
#                 raise HTTPException(
#                     detail="Product name Already Used",
#                     status_code=status.HTTP_409_CONFLICT
#                 )
        
#         result = await update_product_service(
#             product_id=product_id,
#             product_name=data.product_name,
#             product_price=data.product_price,
#             product_description =data.product_description,
#             user_id = user.user_id,
#             current_product_name=current_product_name,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return JSONResponse(content={
#                 "status":1,
#                 "data":result
#             })
        
#         else:
#             raise HTTPException(status_code=500, detail="Failed to Update product.")

#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[product][UPDATE_product] Error: Failed to Update product. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail="Failed to Update product.")
    

@router_v1.put("/{buy_product_id}")
async def canceled_buy_product_id_handler(
    buy_product_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        check_buy_product_id = await check_product_service(
            buy_product_id=buy_product_id,
            session=session,
            background_tasks=background_tasks,
        )

        result = await delete_product_service(
            current_buy_product_name=current_buy_product_name,
            user_id= user.user_id,
            buy_product_id=buy_product_id,
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
    

@app.get("/v1/cart-product")
async def get_price_buy_product_handler(
    background_tasks: BackgroundTasks,
    cart_product_data : List[CartProductData],
    o: Optional[int] = Query(None),
    p: Optional[int] = Query(None),
    # cart_product_offer_data : CartProductOfferData,
    # user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        
        offer_id = o
        promocode_id = p
        if offer_id:
            offer_id = offer_id
            fetch_offer = await get_offer_service(
                offer_id=offer_id,
                session=session,
                background_tasks=background_tasks,
            )
            if fetch_offer["is_deleted"]== False:
                offer_percentage = fetch_offer["offer_percentage"]
            else:
                offer_percentage = None
        else:
            offer_percentage = None


        if promocode_id:
            promocode_id = promocode_id
            fetch_promocode = await get_promocode_service(
                promocode_id=promocode_id,
                session=session,
                background_tasks=background_tasks,
            )
            if fetch_promocode["is_deleted"] == False:
                promocode_amount = fetch_promocode["promocode_percentage"]
            else:
                promocode_amount = None
        else:
            promocode_amount = None


        price_result = await get_price_buy_product_service(
            data = cart_product_data,
            offer_percentage=offer_percentage,
            promocode_amount=promocode_amount,
            session=session,
            background_tasks=background_tasks,
        )

        return JSONResponse(
            content=price_result,
            status_code=200
        )

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
    

app.include_router(router_v1)

# if __name__=="__main__":
#     uvicorn.run("app.microservices.buyed_product.buyed_routes:app", host="0.0.0.0", port=9020,reload=True)


