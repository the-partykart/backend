from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session as get_session
from app.db.models.db_base import Order, OrderItem, OrderShipment, Products
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


@router_v1.post("/calculate-rates")
async def calculate_rates(
    payload: CalculateRatesPayload,
    db: AsyncSession = Depends(get_session)
):
    resp = await client.calculate_rates(db, payload.model_dump())

    if not resp.get("success"):
        raise HTTPException(400, resp.get("message") or resp)

    couriers = resp.get("data", [])

    cheapest = min(couriers, key=lambda x: x["total_shipping_charges"])
    fastest = min(couriers, key=lambda x: x["tat"])

    return {
        "success": True,
        "message": "Rates fetched",
        "cheapest": cheapest,
        "fastest": fastest,
        "all_couriers": couriers
    }


@router_v1.post("/admin/order/{order_id}/shipment")
async def create_shipment_from_order(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Admin creates DRAFT shipment from order items.
    Shipment is immutable after BigShip order creation.
    """

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

    # ❌ Order state validation
    if order.confirm_order_status == "Cancelled":
        raise HTTPException(400, "Cancelled order cannot be shipped")

    if order.delivery_status in ("Shipped", "Delivered"):
        raise HTTPException(400, "Order already shipped")

    if not order.items:
        raise HTTPException(400, "Order has no items")

    # 2️⃣ Check existing shipment
    shipment = (
        await db.execute(
            select(OrderShipment)
            .where(OrderShipment.order_id == order_id)
        )
    ).scalar_one_or_none()

    # 🔒 Lock shipment after creation
    if shipment and shipment.manifest_status in ("created", "manifested"):
        return {
            "success": True,
            "message": "Shipment already finalized",
            "shipment_id": shipment.shipment_id,
            "status": shipment.manifest_status
        }

    # 3️⃣ Calculate dimensions
    try:
        dims = calculate_shipment_from_products(order.items)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 4️⃣ Create or update shipment (DRAFT only)
    shipment_data = {k: v for k, v in dims.items() if k != "calculation_meta"}


    if not shipment:
        shipment = OrderShipment(
            order_id=order_id,
            provider="bigship",
            manifest_status="draft",
            **shipment_data
        )
        db.add(shipment)

        shipment.order_payload = {
            "auto_calculated": True,
            "source": "product_dimensions",
            "item_count": len(order.items),
            "calculated_at": datetime.utcnow().isoformat(),
            "calculation_meta": dims["calculation_meta"]
        }

    else:
        # Allow update ONLY in draft
        # shipment.shipment_weight = dims["shipment_weight"]
        # shipment.shipment_length = dims["shipment_length"]
        # shipment.shipment_width = dims["shipment_width"]
        # shipment.shipment_height = dims["shipment_height"]
        # shipment.shipment_chargeable_weight = dims["shipment_chargeable_weight"]


        shipment.shipment_weight = Decimal(str(dims["shipment_weight"]))
        shipment.shipment_length = Decimal(str(dims["shipment_length"]))
        shipment.shipment_width = Decimal(str(dims["shipment_width"]))
        shipment.shipment_height = Decimal(str(dims["shipment_height"]))
        shipment.shipment_chargeable_weight = Decimal(str(dims["shipment_chargeable_weight"]))


    # 5️⃣ Save calculation audit
    shipment.order_payload = {
        "auto_calculated": True,
        "source": "product_dimensions",
        "item_count": len(order.items),
        "calculated_at": datetime.utcnow().isoformat()
    }

    await db.commit()
    await db.refresh(shipment)

    return {
        "success": True,
        "message": "Shipment ready (DRAFT)",
        "shipment_id": shipment.shipment_id,
        "dimensions": {
            "weight": shipment.shipment_weight,
            "length": shipment.shipment_length,
            "width": shipment.shipment_width,
            "height": shipment.shipment_height,
            "chargeable_weight": shipment.shipment_chargeable_weight
        },
        "next_step": "Calculate rates → Confirm order"
    }



def safe_last_name(name: str) -> str:
    if not name or len(name.strip()) < 3:
        return "Customer"
    return name.strip()



@router_v1.post("/order/create")
async def create_bigship_order(
    order_id: int,
    courier_id: int,
    courier_name: str,
    db: AsyncSession = Depends(get_session)
):
    # 🔒 Lock Order
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.product)
            .selectinload(Products.sub_category)
        )
        .where(Order.order_id == order_id)
        .with_for_update()
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    if order.confirm_order_status == "Cancelled":
        raise HTTPException(400, "Cancelled order cannot be processed")

    if order.confirm_order_status == "Confirmed":
        return {"success": True, "message": "Order already confirmed"}

    # 🔒 Lock Shipment
    result = await db.execute(
        select(OrderShipment)
        .where(OrderShipment.order_id == order_id)
        .with_for_update()
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(400, "Shipment not created")

    if shipment.bigship_system_order_id:
        return {
            "success": True,
            "message": "BigShip order already created",
            "system_order_id": shipment.bigship_system_order_id
        }

    # 📦 Build Payload
    payload = build_bigship_payload(
        order=order,
        shipment=shipment,
        courier_id=courier_id
    )

    shipment.order_payload = payload

    # 🚀 Call BigShip
    response = await client.add_single_order(db, payload)

    # ✅ Persist success
    shipment.bigship_system_order_id = response["data"].split()[-1]
    shipment.bigship_courier_id = courier_id
    shipment.courier_name = courier_name
    shipment.manifest_status = "created"
    shipment.provider_response = response
    shipment.error_message = None

    order.confirm_order_status = "Confirmed"

    await db.commit()

    return {
        "success": True,
        "message": "Order successfully sent to BigShip",
        "system_order_id": shipment.bigship_system_order_id
    }


import re

def sanitize_product_name(name: str) -> str:
    if not name:
        return "Product"

    # Remove everything except allowed chars
    cleaned = re.sub(r"[^a-zA-Z0-9\s\-\/]", "", name)

    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # BigShip min length safety
    if len(cleaned) < 3:
        return "Product"

    return cleaned[:50]  # BigShip safe limit


def split_address(address: str, max_len: int = 49):
    """
    Splits a single address string into address_line1 and address_line2
    without breaking words.
    """
    if not address:
        return "", ""

    address = address.strip()

    if len(address) <= max_len:
        return address, ""

    words = address.split(" ")
    line1_words = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 <= max_len:
            line1_words.append(word)
            current_len += len(word) + 1
        else:
            break

    address_line1 = " ".join(line1_words)
    address_line2 = address[len(address_line1):].strip()

    return address_line1, address_line2



def build_bigship_payload(
    order: Order,
    shipment: OrderShipment,
    courier_id: int
) -> dict:

    addr = order.shipping_address or {}
    if not addr:
        raise ValueError("Shipping address missing")

    name_parts = addr.get("name", "Customer").split(" ", 1)
    first_name = name_parts[0]
    last_name = safe_last_name(
        name_parts[1] if len(name_parts) > 1 else ""
    )


    product_details = []
    total_invoice_amount = 0
    total_collectable_amount = 0

    for item in order.items:
        product = item.product

        invoice_amt = float(item.price_per_unit) * item.quantity
        collectable_amt = invoice_amt if is_cod_order(order) else 0

        product_details.append({
            "product_category": get_product_category(product),
            "product_sub_category": get_product_sub_category(product),
            "product_name": sanitize_product_name(product.product_name),
            "product_quantity": item.quantity,
            "each_product_invoice_amount": invoice_amt,
            "each_product_collectable_amount": collectable_amt,
            "hsn": ""
        })

        total_invoice_amount += invoice_amt
        total_collectable_amount += collectable_amt

    box_details = [{
        "each_box_dead_weight": float(shipment.shipment_weight or 1),
        "each_box_length": int(shipment.shipment_length or 10),
        "each_box_width": int(shipment.shipment_width or 10),
        "each_box_height": int(shipment.shipment_height or 10),
        "each_box_invoice_amount": total_invoice_amount,
        "each_box_collectable_amount": total_collectable_amount,
        "box_count": 1,
        "product_details": product_details
    }]

    full_address = addr.get("address", "")

    address_line1, address_line2 = split_address(full_address)

    return {
        "shipment_category": "b2c",

        "warehouse_detail": {
            "pickup_location_id": int(settings.BIGSHIP_PICKUP_LOCATION_ID),
            "return_location_id": int(settings.BIGSHIP_RETURN_LOCATION_ID)
        },
        

        "consignee_detail": {
            "first_name": first_name,
            "last_name": last_name,
            "company_name": "",
            "contact_number_primary": str(addr.get("phone")),
            "contact_number_secondary": "",
            "email_id": addr.get("email", ""),
            "consignee_address": {
                "address_line1": address_line1,
                "address_line2": address_line2,
                "address_landmark": addr.get("landmark", ""),
                "pincode": str(addr.get("pincode"))
            }
        },

        "order_detail": {
            "invoice_date": order.created_at.isoformat(),
            "invoice_id": f"INV-{order.order_id}",
            "payment_type": map_payment_type(order),
            "shipment_invoice_amount": total_invoice_amount,
            "total_collectable_amount": total_collectable_amount,
            "box_details": box_details,
            "ewaybill_number": "",
            "document_detail": {
                "invoice_document_file": "",
                "ewaybill_document_file": ""
            }
        },

        "courier_id": courier_id
    }



def is_cod_order(order: Order) -> bool:
    return order.payment_method.upper() == "COD"


def map_payment_type(order: Order) -> str:
    return "COD" if is_cod_order(order) else "Prepaid"


def get_product_sub_category(product: Products) -> str:
    if product.sub_category and product.sub_category.sub_category_name:
        return product.sub_category.sub_category_name
    return "Others"


def get_product_category(product: Products) -> str:
    # You do NOT have direct category mapping
    return "Others"


def choose_closest_price(couriers, preferred_price):
    return min(
        couriers,
        key=lambda c: abs(c["total_shipping_charges"] - preferred_price)
    )


@router_v1.get("/order/{order_id}/track/full")
async def track_order_full(
    order_id: int,
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Order
    order = await db.scalar(
        select(Order).where(Order.order_id == order_id)
    )

    if not order:
        raise HTTPException(404, "Order not found")

    # 2️⃣ Shipment
    shipment = await db.scalar(
        select(OrderShipment).where(OrderShipment.order_id == order_id)
    )

    if not shipment or not shipment.bigship_master_awb:
        return {
            "order_id": order.order_id,
            "delivery_status": order.delivery_status,
            "tracking_available": False,
            "message": "Shipment not yet handed to courier"
        }

    # 3️⃣ Call BigShip Tracking API (AWB based)
    tracking_resp = await client.get_tracking(
        db=db,
        tracking_type="awb",
        tracking_id=shipment.bigship_master_awb
    )

    data = tracking_resp.get("data")
    order_detail = data.get("order_detail") if data else None
    scan_histories = data.get("scan_histories", []) if data else []

    # 4️⃣ Hard failure (invalid AWB)
    if not order_detail:
        return {
            "order_id": order.order_id,
            "awb": shipment.bigship_master_awb,
            "delivery_status": order.delivery_status,
            "tracking_available": False,
            "message": tracking_resp.get("message", "Tracking not available")
        }

    # 5️⃣ Normalize tracking response (THIS IS THE KEY)
    tracking_status = order_detail.get("current_tracking_status")
    has_scans = len(scan_histories) > 0

    return {
        "order_id": order.order_id,
        "order_status": order.confirm_order_status,
        "delivery_status": order.delivery_status,

        # 🔑 Always show AWB
        "awb": shipment.bigship_master_awb,
        "courier": order_detail.get("courier_name"),

        # 🔑 Current truth
        "current_status": tracking_status,
        "manifested_at": order_detail.get("order_manifest_datetime"),
        "last_updated": order_detail.get("current_tracking_datetime"),

        # 🔑 Timeline
        "tracking_available": has_scans,
        "scan_histories": scan_histories,

        # 🔑 UX helper
        "message": (
            "Tracking updates will appear once the shipment is scanned"
            if not has_scans
            else "Tracking available"
        ),

        # Optional
        "label_url": shipment.label_url
    }



@router_v1.post("/order/{order_id}/manifest")
async def manifest_bigship_order(
    order_id: int,
    payload: CalculateRatesPayload,
    db: AsyncSession = Depends(get_session)
):
    # ───────────────────────────────────────
    # 1️⃣ Lock shipment row
    # ───────────────────────────────────────
    shipment = await db.scalar(
        select(OrderShipment)
        .where(OrderShipment.order_id == order_id)
        .with_for_update()
    )

    if not shipment:
        raise HTTPException(404, "Shipment not found")

    # 🔁 Already manifested → directly fetch AWB
    if shipment.manifest_status == "manifested":
        awb_resp = await client.get_shipment_data(
            db,
            shipment_data_id=1,
            system_order_id=shipment.bigship_system_order_id
        )

        awb = awb_resp.get("data", {}).get("master_awb")

        return {
            "success": True,
            "message": "Already manifested",
            "awb": awb or shipment.bigship_master_awb,
            "label_url": shipment.label_url
        }

    if shipment.manifest_status != "created":
        raise HTTPException(
            400,
            f"Invalid shipment status {shipment.manifest_status}"
        )

    # ───────────────────────────────────────
    # 2️⃣ Fetch order
    # ───────────────────────────────────────
    order = await db.scalar(
        select(Order).where(Order.order_id == order_id)
    )

    if not order:
        raise HTTPException(404, "Order not found")

    if order.confirm_order_status != "Confirmed":
        raise HTTPException(400, "Order not confirmed by admin")

    if not order.shipping_details:
        raise HTTPException(400, "Shipping details missing")

    preferred = order.shipping_details
    preferred_courier_id = preferred["courier_id"]
    preferred_price = preferred["total_shipping_charges"]

    # ───────────────────────────────────────
    # 3️⃣ Recalculate rates
    # ───────────────────────────────────────
    rate_resp = await client.calculate_rates(db, payload.model_dump())

    if not rate_resp.get("success"):
        raise HTTPException(400, "Unable to calculate shipping rates")

    couriers = rate_resp.get("data", [])
    if not couriers:
        raise HTTPException(400, "No courier serviceable")

    # ───────────────────────────────────────
    # 4️⃣ Sort couriers
    # ───────────────────────────────────────
    def price_distance(c):
        return abs(c["total_shipping_charges"] - preferred_price)

    sorted_couriers = sorted(
        couriers,
        key=lambda c: (
            c["courier_id"] != preferred_courier_id,
            price_distance(c)
        )
    )[:10]  # safety limit

    final_courier = None
    manifest_resp = None
    fallback_reason = None
    last_error = None

    # ───────────────────────────────────────
    # 5️⃣ Try manifest with fallback
    # ───────────────────────────────────────
    for idx, courier in enumerate(sorted_couriers, start=1):
        shipment.bigship_courier_id = courier["courier_id"]

        manifest_payload = {
            "system_order_id": shipment.bigship_system_order_id,
            "courier_id": courier["courier_id"]
        }

        manifest_resp = await client.manifest_single(db, manifest_payload)

        if manifest_resp.get("success"):
            final_courier = courier
            fallback_reason = (
                None
                if courier["courier_id"] == preferred_courier_id
                else f"Fallback courier used at attempt {idx}"
            )
            break

        error_msg = manifest_resp.get("message", "")
        last_error = error_msg.lower()

        if "not serviceable" in last_error:
            continue

        shipment.error_message = error_msg
        await db.commit()
        raise HTTPException(400, error_msg)

    if not final_courier:
        shipment.error_message = last_error or "All couriers failed at manifest"
        await db.commit()
        raise HTTPException(400, shipment.error_message)

    # ───────────────────────────────────────
    # 6️⃣ Save final courier
    # ───────────────────────────────────────
    order.final_shipping_details = {
        **final_courier,
        "fallback_reason": fallback_reason
    }

    # ───────────────────────────────────────
    # 7️⃣ Fetch AWB
    # ───────────────────────────────────────
    awb_resp = await client.get_shipment_data(
        db,
        shipment_data_id=1,
        system_order_id=shipment.bigship_system_order_id
    )

    awb = awb_resp.get("data", {}).get("master_awb")
    label_url = awb_resp.get("data", {}).get("label_url")

    if not awb:
        raise HTTPException(400, "AWB not generated")

    # ───────────────────────────────────────
    # 8️⃣ FINAL SUCCESS STATE UPDATE
    # ───────────────────────────────────────
    shipment.bigship_master_awb = awb
    shipment.label_url = label_url
    shipment.manifest_status = "manifested"
    shipment.manifested_at = datetime.utcnow()
    shipment.provider_response = {
        "manifest": manifest_resp,
        "awb": awb_resp
    }
    shipment.error_message = None

    order.delivery_status = "Shipped"
    order.delivery_tracking_id = awb

    await db.commit()

    # ───────────────────────────────────────
    # 9️⃣ Response
    # ───────────────────────────────────────
    return {
        "success": True,
        "message": "Order manifested successfully",
        "awb": awb,
        "label_url": label_url,
        "final_courier": final_courier["courier_name"],
        "fallback_used": fallback_reason is not None
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
    Cancel order:
    - Before manifest → DB only
    - After manifest (before pickup) → Cancel AWB + DB
    """

    # 1️⃣ Fetch order
    order = await db.scalar(
        select(Order).where(Order.order_id == order_id)
    )
    if not order:
        raise HTTPException(404, "Order not found")

    # ❌ Delivered orders cannot be cancelled
    if order.delivery_status == "Delivered":
        raise HTTPException(400, "Delivered orders cannot be cancelled")

    # 2️⃣ Fetch shipment (lock)
    shipment = await db.scalar(
        select(OrderShipment)
        .where(OrderShipment.order_id == order_id)
        .with_for_update()
    )

    if not shipment:
        raise HTTPException(404, "Shipment not found")

    # ✅ Idempotency
    if order.delivery_status == "Cancelled":
        return {
            "success": True,
            "message": "Order already cancelled"
        }

    # ===============================
    # CASE 1️⃣ : Cancel BEFORE manifest
    # ===============================
    if not shipment.bigship_master_awb:
        shipment.manifest_status = "cancelled"
        shipment.error_message = None
        shipment.provider_response = {
            "note": "Cancelled before manifest, BigShip not called"
        }

        order.confirm_order_status = "Cancelled"
        order.delivery_status = "Cancelled"
        order.delivery_tracking_id = None

        await db.commit()

        return {
            "success": True,
            "message": "Order cancelled"
        }

    # ===============================
    # CASE 2️⃣ : Cancel AFTER manifest
    # ===============================
    cancel_resp = await client.cancel_awb(
        db=db,
        awbs=[shipment.bigship_master_awb]
    )

    if not cancel_resp.get("success"):
        shipment.error_message = cancel_resp.get("message", "Cancel failed")
        await db.commit()
        raise HTTPException(400, shipment.error_message)

    cancel_data = cancel_resp.get("data", [])
    awb_result = next(
        (x for x in cancel_data if x["master_awb"] == shipment.bigship_master_awb),
        None
    )

    if not awb_result:
        shipment.error_message = "AWB cancellation response missing"
        await db.commit()
        raise HTTPException(400, shipment.error_message)

    # 3️⃣ Persist cancellation
    shipment.manifest_status = "cancelled"
    shipment.provider_response = cancel_resp
    shipment.error_message = None
    shipment.bigship_master_awb = None
    shipment.label_url = None

    order.confirm_order_status = "Cancelled"
    order.delivery_status = "Cancelled"
    order.delivery_tracking_id = None

    await db.commit()

    return {
        "success": True,
        "message": awb_result.get("cancel_response", "Order cancelled successfully"),
        "order_id": order.order_id
    }
