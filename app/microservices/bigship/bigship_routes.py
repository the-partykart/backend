# # app/microservices/bigship/bigship_routes.py

# from contextlib import asynccontextmanager
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from app.db.db_session import get_async_session as get_session
# from app.db.models.db_base import Order
# from app.microservices.bigship.bigship_service import BigShipClient
# from app.microservices.bigship.bigship_schema import (
#     WarehouseAdd,
#     AddSingleOrderPayload,
#     ManifestPayload,
#     AWBRequest,
#     CancelPayload,
#     CalculateRatesPayload,
#     TrackingQuery
# )
# from config.config import settings


# # --------------------------------------------------------------------
# # BIGSHIP CLIENT (shared instance)
# # --------------------------------------------------------------------
# client = BigShipClient()


# # --------------------------------------------------------------------
# # LIFESPAN HANDLER (REPLACES on_event STARTUP/SHUTDOWN)
# # --------------------------------------------------------------------
# @asynccontextmanager
# async def bigship_lifespan(app):
#     # Optional startup logic here
#     try:
#         yield
#     finally:
#         # Clean shutdown: close HTTPX session
#         await client.close()


# # --------------------------------------------------------------------
# # ROUTER
# # --------------------------------------------------------------------
# global_prefix = settings.global_prefix

# router_v1 = APIRouter(
#     prefix=f"/{global_prefix}/bigship",
#     tags=["BigShip"],
#     lifespan=bigship_lifespan
# )


# @router_v1.post("/confirm/{order_id}")
# async def confirm_bigship_order(order_id: int, db: AsyncSession = Depends(get_session)):

#     # 1. Fetch user order & items
#     order = await fetch_order(order_id)
#     items = await fetch_order_items(order_id)

#     # 2. Build BigShip payload from DB
#     bs_payload = build_bigship_payload(order, items)

#     # 3. Create order on BigShip
#     create_resp = await client.add_single_order(db, bs_payload)
#     if not create_resp["success"]:
#         return error(create_resp["message"])

#     system_order_id = extract(create_resp["data"])

#     # 4. Save mapping to DB
#     save_system_order_id(order_id, system_order_id)

#     # 5. Manifest
#     manifest_resp = await client.manifest_single(db, {
#         "system_order_id": system_order_id
#     })

#     if not manifest_resp["success"]:
#         return {
#             "success": True,
#             "message": "Order created but manifest failed.",
#             "system_order_id": system_order_id
#         }

#     # 6. Get AWB
#     awb_data = await client.get_shipment_data(db, 1, system_order_id)

#     # 7. Save AWB + courier
#     update_order_with_awb(order_id, awb_data)

#     return {
#         "success": True,
#         "system_order_id": system_order_id,
#         "master_awb": awb_data.get("master_awb"),
#         "courier_id": awb_data.get("courier_id")
#     }


# # --------------------------------------------------------------------
# # 1) FORCE REFRESH TOKEN
# # --------------------------------------------------------------------
# @router_v1.post("/auth/refresh-token")
# async def refresh_token(db: AsyncSession = Depends(get_session)):
#     try:
#         token = await client.get_token(db)
#         return {"success": True, "token": token}
#     except Exception as e:
#         raise HTTPException(500, str(e))


# # --------------------------------------------------------------------
# # 2) ADD WAREHOUSE
# # --------------------------------------------------------------------
# @router_v1.post("/warehouse/add")
# async def add_warehouse(payload: WarehouseAdd, db: AsyncSession = Depends(get_session)):
#     resp = await client.add_warehouse(db, payload.model_dump())

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     return resp


# # --------------------------------------------------------------------
# # 3) WAREHOUSE LIST
# # --------------------------------------------------------------------
# @router_v1.get("/warehouse/list")
# async def warehouse_list(
#     page_index: int = 1,
#     page_size: int = 50,
#     db: AsyncSession = Depends(get_session)
# ):
#     resp = await client.get_warehouse_list(db, page_index, page_size)

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     return resp


# # --------------------------------------------------------------------
# # 4) CREATE ORDER (SINGLE SHIPMENT)
# # --------------------------------------------------------------------
# @router_v1.post("/order/create")
# async def create_order(payload: AddSingleOrderPayload, db: AsyncSession = Depends(get_session)):
#     bs_payload = payload.model_dump()
#     resp = await client.add_single_order(db, bs_payload)

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     # Extract system_order_id
#     raw = resp.get("data")
#     import re
#     match = re.search(r"(\d+)", raw) if isinstance(raw, str) else None
#     sys_order_id = match.group(1) if match else str(raw)

#     # Save to DB
#     new_order = Order(
#         order_id=f"local-{int(__import__('time').time())}",
#         customer_name=payload.consignee_detail.get("first_name"),
#         total_amount=payload.order_detail.get("shipment_invoice_amount"),
#         shipping_address=payload.consignee_detail.get("consignee_address"),
#         bigship_system_order_id=sys_order_id
#     )

#     db.add(new_order)
#     await db.commit()
#     await db.refresh(new_order)

#     return {
#         "success": True,
#         "system_order_id": sys_order_id,
#         "local_order_id": new_order.order_id
#     }


# # --------------------------------------------------------------------
# # 5) MANIFEST ORDER (GENERATES AWB)
# # --------------------------------------------------------------------
# @router_v1.post("/order/manifest")
# async def manifest_order(payload: ManifestPayload, db: AsyncSession = Depends(get_session)):
#     resp = await client.manifest_single(db, payload.model_dump())

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     # Fetch AWB after manifesting
#     awb_resp = await client.get_shipment_data(
#         db,
#         shipment_data_id=1,      # AWB ID
#         system_order_id=payload.system_order_id
#     )

#     if awb_resp.get("success"):
#         data = awb_resp.get("data", {})
#         master_awb = data.get("master_awb")
#         courier_id = data.get("courier_id")

#         # Update DB
#         result = await db.execute(
#             select(Order).where(Order.bigship_system_order_id == str(payload.system_order_id))
#         )
#         order = result.scalars().first()

#         if order:
#             order.bigship_master_awb = master_awb
#             order.bigship_courier_id = courier_id
#             await db.commit()

#         return {
#             "success": True,
#             "master_awb": master_awb,
#             "courier_id": courier_id
#         }

#     return {
#         "success": True,
#         "message": "Manifest done, but AWB fetch failed.",
#         "awb_response": awb_resp
#     }


# # --------------------------------------------------------------------
# # 6) GET LABEL / AWB / MANIFEST FILE
# # --------------------------------------------------------------------
# @router_v1.post("/order/shipment-data")
# async def get_shipment_data(req: AWBRequest, db: AsyncSession = Depends(get_session)):
#     resp = await client.get_shipment_data(
#         db,
#         shipment_data_id=req.shipment_data_id,
#         system_order_id=req.system_order_id
#     )

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     data = resp.get("data")

#     # Save PDF (Base64) in DB if available
#     if data.get("res_FileContent"):
#         result = await db.execute(
#             select(Order).where(Order.bigship_system_order_id == str(req.system_order_id))
#         )
#         order = result.scalars().first()

#         if order:
#             order.label_pdf_base64 = data["res_FileContent"]
#             await db.commit()

#     return data


# # --------------------------------------------------------------------
# # 7) CANCEL AWB
# # --------------------------------------------------------------------
# @router_v1.put("/order/cancel")
# async def cancel_awb(payload: CancelPayload, db: AsyncSession = Depends(get_session)):
#     resp = await client.cancel_awb(db, payload.awbs)

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     return resp


# # --------------------------------------------------------------------
# # 8) TRACKING STATUS
# # --------------------------------------------------------------------
# @router_v1.get("/tracking")
# async def tracking(
#     tracking_type: str,
#     tracking_id: str,
#     db: AsyncSession = Depends(get_session)
# ):
#     return await client.get_tracking(db, tracking_type, tracking_id)


# # --------------------------------------------------------------------
# # 9) CALCULATE RATES (PRE-ORDER)
# # --------------------------------------------------------------------
# @router_v1.post("/calculate-rates")
# async def calculate_rates(payload: CalculateRatesPayload, db: AsyncSession = Depends(get_session)):
#     resp = await client.calculate_rates(db, payload.model_dump())

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     return resp


# # --------------------------------------------------------------------
# # 10) SHIPPING RATES (AFTER ORDER CREATION)
# # --------------------------------------------------------------------
# @router_v1.get("/shipping-rates")
# async def shipping_rates(
#     shipment_category: str,
#     system_order_id: int,
#     risk_type: str | None = None,
#     db: AsyncSession = Depends(get_session)
# ):
#     resp = await client.get_shipping_rates(
#         db,
#         shipment_category,
#         system_order_id,
#         risk_type
#     )

#     if not resp.get("success"):
#         raise HTTPException(400, resp.get("message") or resp)

#     return resp




from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session as get_session
from app.db.models.db_base import Order, OrderItem, OrderShipment
from app.microservices.bigship.bigship_service import BigShipClient, calculate_shipment_from_products
from app.microservices.bigship.bigship_schema import CalculateRatesPayload, CreateShipmentPayload, WarehouseAdd
from config.config import settings
from sqlalchemy.orm import selectinload


client = BigShipClient()

@asynccontextmanager
async def bigship_lifespan(app):
    try:
        yield
    finally:
        await client.close()

router_v1 = APIRouter(
    prefix=f"/{settings.global_prefix}/bigship",
    tags=["BigShip"],
    lifespan=bigship_lifespan
)

# -----------------------------
# LOGIN (Step 1)
# -----------------------------
@router_v1.post("/login")
async def bigship_login(db: AsyncSession = Depends(get_session)):
    try:
        token = await client.force_refresh_token(db)
        return {
            "success": True,
            "message": "Login successful",
            "token": token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# ADD WAREHOUSE (Step 2)
# -----------------------------
@router_v1.post("/warehouse/add")
async def add_warehouse(payload: WarehouseAdd, db: AsyncSession = Depends(get_session)):
    resp = await client.add_warehouse(db, payload.model_dump())

    if not resp.get("success"):
        raise HTTPException(400, resp.get("message") or resp)

    return resp


# -----------------------------
# WAREHOUSE LIST
# -----------------------------
@router_v1.get("/warehouse/list")
async def warehouse_list(
    page_index: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_session)
):
    resp = await client.get_warehouse_list(db, page_index, page_size)

    if not resp.get("success"):
        raise HTTPException(400, resp.get("message") or resp)

    return resp



# # -----------------------------
# # CALCULATE RATES (Step 4)
# # -----------------------------
# @router_v1.post("/calculate-rates")
# async def calculate_rates(payload: CalculateRatesPayload, db: AsyncSession = Depends(get_session)):
#     try:
#         resp = await client.calculate_rates(db, payload.model_dump())

#         if not resp.get("success"):
#             raise HTTPException(400, resp.get("message") or resp)

#         couriers = resp.get("data", [])

#         # ----------------------------
#         # 1) Cheapest Courier
#         # ----------------------------
#         cheapest = min(couriers, key=lambda x: x["total_shipping_charges"])

#         # ----------------------------
#         # 2) Fastest Courier (lowest TAT)
#         # ----------------------------
#         fastest = min(couriers, key=lambda x: x["tat"])

#         return {
#             "success": True,
#             "message": "Rates fetched",
#             "cheapest": cheapest,
#             "fastest": fastest,
#             "all_couriers": couriers     # Optional
#         }

#     except Exception as e:
#         raise HTTPException(500, str(e))

# -----------------------------
# CALCULATE RATES (Step 4)
# -----------------------------
@router_v1.post("/calculate-rates")
async def calculate_rates(
    payload: CalculateRatesPayload,
    db: AsyncSession = Depends(get_session)
):
    try:
        # 1️⃣ First attempt
        resp = await client.calculate_rates(db, payload.model_dump())

        # 🔁 Auto relogin on token expiry
        if not resp.get("success") and "token" in str(resp).lower():
            # Refresh token
            await client.force_refresh_token(db)

            # Retry once
            resp = await client.calculate_rates(db, payload.model_dump())

        # ❌ Still failed
        if not resp.get("success"):
            raise HTTPException(400, resp.get("message") or resp)

        couriers = resp.get("data", [])

        # ----------------------------
        # 1) Cheapest Courier
        # ----------------------------
        cheapest = min(couriers, key=lambda x: x["total_shipping_charges"])

        # ----------------------------
        # 2) Fastest Courier
        # ----------------------------
        fastest = min(couriers, key=lambda x: x["tat"])

        return {
            "success": True,
            "message": "Rates fetched",
            "cheapest": cheapest,
            "fastest": fastest,
            "all_couriers": couriers
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))



@router_v1.post("/admin/order/{order_id}/shipment")
async def create_shipment_from_order(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Fetch order + items + products
    order = (
        await db.execute(
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.product)
            )
            .where(Order.order_id == order_id)
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    if not order.items:
        raise HTTPException(400, "Order has no items")

    # 2️⃣ Prevent duplicate shipment
    existing = (
        await db.execute(
            select(OrderShipment)
            .where(OrderShipment.order_id == order_id)
        )
    ).scalar_one_or_none()

    if existing:
        return {
            "success": True,
            "message": "Shipment already exists",
            "shipment_id": existing.shipment_id
        }

    # 3️⃣ Auto-calculate shipment
    try:
        dims = calculate_shipment_from_products(order.items)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 4️⃣ Create shipment (DRAFT)
    shipment = OrderShipment(
        order_id=order_id,
        provider="bigship",
        manifest_status="draft",
        **dims,
        order_payload={
            "auto_calculated": True,
            "source": "products"
        }
    )

    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)

    return {
        "success": True,
        "message": "Shipment auto-created from order",
        "shipment_id": shipment.shipment_id,
        "dimensions": dims
    }



# @router_v1.post("/order/create")
# async def create_bigship_order(
#     order_id: int,
#     courier_id: int,
#     courier_name: str,
#     db: AsyncSession = Depends(get_session)
# ):
#     # 1️⃣ Fetch order
#     result = await db.execute(
#         select(Order).where(Order.order_id == order_id)
#     )
#     order = result.scalar_one_or_none()

#     if not order:
#         raise HTTPException(404, "Order not found")

#     # 2️⃣ Fetch shipment
#     result = await db.execute(
#         select(OrderShipment).where(OrderShipment.order_id == order_id)
#     )
#     shipment = result.scalar_one_or_none()

#     if not shipment:
#         raise HTTPException(400, "Shipment not created yet")

#     # 🔐 Prevent duplicate BigShip orders
#     if shipment.bigship_system_order_id:
#         return {
#             "success": True,
#             "message": "BigShip order already created",
#             "system_order_id": shipment.bigship_system_order_id
#         }

#     # 3️⃣ Build payload
#     payload = {
#         "shipment_category": "b2c",
#         "warehouse_detail": {
#             "pickup_location_id": int(settings.BIGSHIP_PICKUP_LOCATION_ID),
#             "return_location_id": int(settings.BIGSHIP_RETURN_LOCATION_ID),
#         },
#         "order_detail": {
#             "shipment_invoice_amount": float(order.final_amount)
#         },
#         "courier_id": courier_id
#     }

#     shipment.order_payload = payload

#     # 4️⃣ Call BigShip
#     resp = await client.add_single_order(db, payload)

#     if not resp.get("success"):
#         shipment.error_message = resp.get("message")
#         await db.commit()
#         raise HTTPException(400, resp.get("message") or resp)

#     # 5️⃣ Save response
#     shipment.bigship_system_order_id = resp.get("system_order_id")
#     shipment.bigship_courier_id = courier_id
#     shipment.courier_name = courier_name
#     shipment.manifest_status = "created"
#     shipment.provider_response = resp

#     await db.commit()

#     return {
#         "success": True,
#         "message": "Order created in BigShip",
#         "system_order_id": shipment.bigship_system_order_id
#     }


@router_v1.post("/order/create")
async def create_bigship_order(
    order_id: int,
    courier_id: int,
    courier_name: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Admin confirms order → creates BigShip order
    """

    # 1️⃣ Fetch order
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    # ❌ Prevent re-confirm
    if order.confirm_order_status == "Confirmed":
        return {
            "success": True,
            "message": "Order already confirmed",
        }

    # 2️⃣ Fetch shipment
    result = await db.execute(
        select(OrderShipment).where(OrderShipment.order_id == order_id)
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(400, "Shipment not created yet")

    # 🔐 Prevent duplicate BigShip orders
    if shipment.bigship_system_order_id:
        order.confirm_order_status = "Confirmed"
        await db.commit()
        await db.refresh(shipment)
        await db.refresh(order)  

        return {
            "success": True,
            "message": "BigShip order already created",
            "system_order_id": shipment.bigship_system_order_id
        }

    # 3️⃣ Build BigShip payload
    payload = {
        "shipment_category": "b2c",
        "warehouse_detail": {
            "pickup_location_id": int(settings.BIGSHIP_PICKUP_LOCATION_ID),
            "return_location_id": int(settings.BIGSHIP_RETURN_LOCATION_ID),
        },
        "order_detail": {
            "shipment_invoice_amount": float(order.final_amount)
        },
        "courier_id": courier_id
    }

    shipment.order_payload = payload

    # 4️⃣ Call BigShip
    resp = await client.add_single_order(db, payload)

    # ❌ FAILURE CASE
    if not resp.get("success"):
        shipment.error_message = resp.get("message")
        shipment.manifest_status = "pending"

        # order remains Pending
        order.confirm_order_status = "Pending"

        await db.commit()
        raise HTTPException(400, resp.get("message") or "BigShip order failed")

    # ✅ SUCCESS CASE
    shipment.bigship_system_order_id = resp.get("system_order_id")
    shipment.bigship_courier_id = courier_id
    shipment.courier_name = courier_name
    shipment.manifest_status = "created"
    shipment.provider_response = resp
    shipment.error_message = None

    # 🔥 IMPORTANT UPDATE
    order.confirm_order_status = "Confirmed"

    await db.commit()
    await db.refresh(shipment)
    await db.refresh(order)   # 🔥 VERY IMPORTANT



    return {
        "success": True,
        "message": "Order successfully sent to BigShip",
        "system_order_id": shipment.bigship_system_order_id
    }



@router_v1.post("/order/{order_id}/manifest")
async def manifest_bigship_order(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Shipment
    result = await db.execute(
        select(OrderShipment).where(OrderShipment.order_id == order_id)
    )
    shipment = result.scalar_one_or_none()

    if not shipment or not shipment.bigship_system_order_id:
        raise HTTPException(400, "BigShip order not created")

    if shipment.manifest_status == "manifested":
        return {
            "success": True,
            "awb": shipment.bigship_master_awb
        }

    # 2️⃣ Manifest
    resp = await client.manifest_single(db, {
        "system_order_id": shipment.bigship_system_order_id,
        "courier_id": shipment.bigship_courier_id
    })

    if not resp.get("success"):
        raise HTTPException(400, "Manifest failed")

    # 3️⃣ Fetch AWB
    awb_resp = await client.get_shipment_data(
        db,
        shipment_data_id=1,
        system_order_id=shipment.bigship_system_order_id
    )

    awb = awb_resp["data"]["master_awb"]

    # 4️⃣ Save
    shipment.bigship_master_awb = awb
    shipment.label_url = awb_resp["data"]["label_url"]
    shipment.manifest_status = "manifested"
    shipment.manifested_at = datetime.utcnow()
    shipment.provider_response = awb_resp

    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if order:
        order.delivery_status = "Shipped"
        order.delivery_tracking_id = awb

    await db.commit()

    return {
        "success": True,
        "awb": awb,
        "label_url": shipment.label_url
    }


@router_v1.get("/order/{order_id}/track")
async def track_order(order_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    return {
        "order_id": order.order_id,
        "order_status": order.confirm_order_status,
        "delivery_status": order.delivery_status,
        "tracking_id": order.delivery_tracking_id
    }



@router_v1.get("/order/{order_id}/track/full")
async def track_order_full(order_id: int, db: AsyncSession = Depends(get_session)):
    # 1️⃣ Order
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    # 2️⃣ Shipment
    result = await db.execute(
        select(OrderShipment).where(OrderShipment.order_id == order_id)
    )
    shipment = result.scalar_one_or_none()

    if not shipment or not shipment.bigship_master_awb:
        return {
            "order_id": order.order_id,
            "status": order.delivery_status,
            "message": "Shipment not yet handed to courier"
        }

    # 3️⃣ (Dummy) BigShip tracking response
    tracking_data = {
        "current_status": "In Transit",
        "last_location": "Mumbai Hub",
        "last_updated": "2025-01-12 18:30",
        "expected_delivery": "2025-01-14"
    }

    return {
        "order_id": order.order_id,
        "order_status": order.confirm_order_status,
        "delivery_status": order.delivery_status,
        "courier": shipment.courier_name,
        "awb": shipment.bigship_master_awb,
        "tracking": tracking_data,
        "label_url": shipment.label_url
    }



@router_v1.post("/order/{order_id}/refresh-tracking")
async def refresh_tracking(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    shipment = (
        await db.execute(
            select(OrderShipment).where(OrderShipment.order_id == order_id)
        )
    ).scalar_one_or_none()

    if not shipment or not shipment.bigship_master_awb:
        raise HTTPException(400, "AWB not found")

    resp = await client.track_awb(db, shipment.bigship_master_awb)

    if not resp.get("success"):
        raise HTTPException(400, "Tracking failed")

    data = resp["data"]

    shipment.tracking_status = data["current_status"]
    shipment.tracking_location = data["last_location"]
    shipment.tracking_last_updated = datetime.strptime(
        data["last_updated"], "%Y-%m-%d %H:%M"
    )
    shipment.expected_delivery_date = datetime.strptime(
        data["expected_delivery"], "%Y-%m-%d"
    ).date()

    shipment.tracking_raw_response = resp

    # Update order delivery status
    order = (
        await db.execute(
            select(Order).where(Order.order_id == order_id)
        )
    ).scalar_one()

    order.delivery_status = data["current_status"]

    await db.commit()

    return {
        "success": True,
        "message": "Tracking refreshed"
    }



async def refresh_all_active_shipments(db: AsyncSession):
    shipments = (
        await db.execute(
            select(OrderShipment)
            .where(OrderShipment.manifest_status == "manifested")
        )
    ).scalars().all()

    for shipment in shipments:
        await client.track_awb(db, shipment.bigship_master_awb)



@router_v1.post("/order/{order_id}/cancel")
async def cancel_bigship_order(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Admin cancels BigShip shipment (before pickup)
    """

    # 1️⃣ Fetch order
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    # 2️⃣ Fetch shipment
    result = await db.execute(
        select(OrderShipment).where(OrderShipment.order_id == order_id)
    )
    shipment = result.scalar_one_or_none()

    if not shipment or not shipment.bigship_system_order_id:
        raise HTTPException(400, "BigShip order not created")

    # ❌ Already cancelled
    if shipment.manifest_status == "cancelled":
        return {
            "success": True,
            "message": "Order already cancelled"
        }

    # ❌ If already delivered
    if order.delivery_status == "Delivered":
        raise HTTPException(400, "Delivered orders cannot be cancelled")

    # 3️⃣ Call BigShip cancel
    resp = await client.cancel_single_order(db, {
        "system_order_id": shipment.bigship_system_order_id
    })

    if not resp.get("success"):
        shipment.error_message = resp.get("message")
        await db.commit()
        raise HTTPException(400, resp.get("message") or "Cancel failed")

    # 4️⃣ Update shipment
    shipment.manifest_status = "cancelled"
    shipment.provider_response = resp
    shipment.error_message = None

    # 5️⃣ Update order
    order.confirm_order_status = "Cancelled"
    order.delivery_status = "Cancelled"

    await db.commit()

    return {
        "success": True,
        "message": "Order cancelled successfully"
    }
