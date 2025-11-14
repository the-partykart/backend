from fastapi import Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.services.buy_product_repository import buy_product_db, get_all_buy_product_db, get_buy_product_db
from app.db.services.order_alert_repository import new_order_db
from app.db.services.products_repository import create_product_db, delete_product_db, get_all_product_db, get_product_db, update_product_db
from app.microservices.common_function import build_admin_order_email, object_to_dict, send_admin_notification_async
from app.microservices.products.products_service import get_product_service
from app.utility.logging_utils import log_async 

from datetime import datetime



from datetime import datetime

async def generate_order_id(user_id: int) -> str:
    # Current datetime
    now = datetime.now()
    
    # Format: YYYYMMDDHHMMSS
    timestamp = now.strftime("%Y%m%d%H%M%S")
    
    # Combine with user_id
    order_id = f"{timestamp}{user_id}"
    
    return order_id

# #--------------------------------------------------------------------------------------------------------------



from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.db.models.db_base import Order, OrderItem, Products, OrderAlert, Users



async def create_order(
        data, user_id: int, 
        session: AsyncSession,
        background_tasks:BackgroundTasks
):
    total_amount = 0
    items_data = []

    # 1️⃣ Calculate total based on backend product prices
    for item in data.items:
        product = await session.scalar(
            select(Products).where(Products.product_id == item.product_id, Products.is_deleted == False)
        )

        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.product_name}")

        # ✅ Use correct field name `product_price`
        subtotal = float(product.product_price) * item.quantity
        total_amount += subtotal

        items_data.append({
            "product": product,
            "product_name": product.product_name,
            "quantity": item.quantity,
            "price_per_unit": product.product_price,
            "subtotal": subtotal
        })

    # 2️⃣ Create the order
    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        discount_amount=0,
        final_amount=total_amount,  # you can adjust later for promo
        payment_method=data.payment_method,
        payment_status="Pending",
        delivery_status="Pending",
        shipping_address=data.shipping_address,
    )
    session.add(order)
    await session.flush()  # ✅ ensures order_id is available

    # 3️⃣ Add each order item & update product stock
    for item_data in items_data:
        session.add(OrderItem(
            order_id=order.order_id,
            product_id=item_data["product"].product_id,
            product_name=item_data["product_name"],
            quantity=item_data["quantity"],
            price_per_unit=item_data["price_per_unit"],
            subtotal=item_data["subtotal"]
        ))

        # ✅ Reduce stock in backend
        item_data["product"].stock -= item_data["quantity"]

    # 4️⃣ Log initial order alert
    session.add(OrderAlert(
        order_id=order.order_id,
        alert_type="ORDER_PLACED",
        alert_message=f"Order {order.order_id} placed successfully."
    ))

    await session.commit()
    await session.refresh(order)
    
    # user = await session.scalar(select(Users).where(Users.user_id == user_id))
    user = await session.scalar(select(Users).where(Users.user_id == user_id, Users.is_deleted == False))

    html_body = build_admin_order_email(order, user, items_data)

    background_tasks.add_task(
        send_admin_notification_async,
        "thepartykart.service@gmail.com",
        "tpjynacphveleaek",
        # "sandeshmorea.c.patil@gmail.com",
        ["sandeshmorea.c.patil@gmail.com", "thepartykart.service@gmail.com"],
        f"🛍️ New Order #{order.order_id} Received — The PartyKart",
        html_body
    )

    return order



































































# #--------------------------------------------------------------------------------------------------------------

# Validation
async def buy_product_service(
        product_id: int,
        product_price: int,
        quantity:int,
        sub_category_id: int,
        offer_id: int,
        offer_percentage : int,
        promocode_id : int,
        promocode_amount,
        shipping_address : str,
        payment_method : str,
        payment_status : str,
        order_id,
        user_id :int,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:

        result = await buy_product_db(
            product_id= product_id,
            product_price= product_price,
            sub_category_id = sub_category_id,
            quantity=quantity,
            offer_id= offer_id,
            offer_percentage = offer_percentage,
            promocode_id = promocode_id,
            promocode_amount= promocode_amount,
            shipping_address = shipping_address,
            payment_method = payment_method,
            payment_status = payment_status,
            order_id=order_id,
            user_id = user_id,
            session=session,
            background_tasks=background_tasks,
        )


        if result:
            
            return True

        # if not result or result is None:
        #     raise HTTPException(detail="product Not Found", status_code= status.HTTP_404_NOT_FOUND)
        # elif result and result.is_deleted==True:
        #     raise HTTPException(detail="product Not Found (product Deleted)", status_code= status.HTTP_404_NOT_FOUND)
        # else:
        #     return result

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create product: {e}"
        )


async def create_buy_product_service(
        product_name,
        product_price,
        product_description,
        user_id,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await create_buy_product_db(
            product_name = product_name,
            product_price = product_price,
            product_description =  product_description,
            user_id = user_id,
            session = session,
            background_tasks = background_tasks,
        )

        if result:
            return {
                "status":1,
                "message":"product create successfully"
                }
        
        else:
            return False
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][CREATE_product_SERVICE] Error in create product Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create product: {e}"
        )

async def get_all_buy_product_service(
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_all_buy_product_db(
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
                message=f"[product][GET_ALL_product] Error: Failed Logic to Fetch all product. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch all product.")


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
    


async def get_buy_product_service(
        buy_product_id:int,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        result = await get_buy_product_db(
            buy_product_id=buy_product_id,
            session=session,
            background_tasks=background_tasks
            )
        
        if result:
            data = {
                col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
                for col in result.__table__.columns
            }
            return data
            # data = {
            # "product_id": result.product_id,
            # "product_name": result.product_name,
            # "created_by": result.created_by,
            # "created_at": result.created_at.isoformat() if result.created_at else None,
            # "updated_by": result.updated_by,
            # "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            # "is_deleted": result.is_deleted,
            # "deleted_by": result.deleted_by,
            # "deleted_at": result.deleted_at.isoformat() if result.deleted_at else None,
            # }
            # return data
        
        if result is None:
            return None
        
        else:
            log_async(
                background_tasks=background_tasks,
                message=f"[product][GET_product] Error: Failed Logic to Fetch buy_product_id. Exception: {e}",
                level="error",
                always_sync=True
            )
            raise HTTPException(status_code=500, detail="Failed Logic to Fetch buy_product_id.")


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
        product_price,
        product_description,
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
            product_description=product_description,
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
        log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][CREATE_product_SERVICE] Error in create product Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Create product: {e}"
        )
    
async def delete_buy_product_service(
    buy_product,
    user_id,
    current_product_name,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
):
    try:
        result = await delete_buy_product_db(
            buy_product = buy_product,
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
        log_async(
            background_tasks=background_tasks,
            message=f"[product_SERVICE][DELETE_product_SERVICE] Error in Delete buy_product Service: Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(
            status_code=404,
            detail=f"Error in Delete product: {e}"
        )
    

async def get_price_buy_product_service(
        data,
        offer_percentage,
        promocode_amount,
        session:AsyncSession,
        background_tasks: BackgroundTasks,
):
    try:
        total_product_price = 0
        discounted_price = 0
        # applyed_offer_percentage = 
        # applyed_promocode_amount = 
        total_saving = 0

        product_pricing = []

        for item in data:
            product_id = item.product_id          

            result = await get_product_service(
                product_id=product_id,
                session=session,
                background_tasks=background_tasks,
            )
            product_price = result["product_price"]

            # product_quantity= result["product_quantity"]
            product_quantity = item.product_quantity
            price = float(product_price*product_quantity)

            product_pricing.append(price)
        
        amount = float(sum(product_pricing))
        total_product_price = amount
        final_amount = amount


        if offer_percentage:
            final_amount = float(final_amount - (final_amount * offer_percentage / 100))
            total_saving = float((total_product_price * offer_percentage / 100))

        if promocode_amount:
            final_amount = float(final_amount-promocode_amount)
            total_saving += promocode_amount

        price_data = {
            "total_product_price":total_product_price,
            "applyed_offer_percentage": f"{offer_percentage} %",
            "applyed_promocode_amount": promocode_amount,
            "final_amount": final_amount,
            "total_saving": total_saving
        }

        return price_data

        
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

