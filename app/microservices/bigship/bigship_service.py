# from fastapi import Depends, HTTPException, BackgroundTasks, status
# from fastapi.responses import JSONResponse
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.db.db_session import get_async_session
# from app.db.services.category_repository import create_category_db, create_sub_category_db, delete_sub_category_db, get_all_sub_category_db, get_category_db, delete_category_db, get_all_category_db, get_category_details_db, get_sub_category_db, update_category_db, update_sub_category_db
# from app.microservices.common_function import object_to_dict
# from app.utility.logging_utils import log_async 

# from datetime import datetime


# # services/bigship_client.py

# import os
# import httpx
# import asyncio
# import re
# from datetime import datetime, timedelta

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from app.db.models.db_base import BigShipToken



# # -----------------------------------------
# # ENV SETTINGS
# # -----------------------------------------
# BASE_URL = os.getenv("BIGSHIP_BASE_URL", "https://api.bigship.in")
# USERNAME = os.getenv("BIGSHIP_USERNAME")
# PASSWORD = os.getenv("BIGSHIP_PASSWORD")
# ACCESS_KEY = os.getenv("BIGSHIP_ACCESS_KEY")

# if not USERNAME or not PASSWORD or not ACCESS_KEY:
#     raise RuntimeError("❌ Missing BigShip environment variables.")


# # Simple rate limit: BigShip = 100 req/min
# RATE_LIMIT_SLEEP = 0.6


# # ===================================================================
# #                        BIGSHIP CLIENT
# # ===================================================================
# class BigShipClient:
#     def __init__(self):
#         self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)

#     async def close(self):
#         await self.client.aclose()

#     # ================================================================
#     # TOKEN MANAGEMENT
#     # ================================================================
#     async def _get_saved_token(self, db: AsyncSession):
#         query = await db.execute(
#             select(BigShipToken).order_by(BigShipToken.id.desc()).limit(1)
#         )
#         return query.scalars().first()

#     async def _save_token(self, db: AsyncSession, token: str):
#         obj = BigShipToken(
#             token=token,
#             expires_at=datetime.utcnow() + timedelta(hours=12)
#         )
#         db.add(obj)
#         await db.commit()

#     async def get_token(self, db: AsyncSession) -> str:
#         """
#         Returns valid token from DB or generates new one.
#         """

#         # Check saved token
#         token_row = await self._get_saved_token(db)

#         if token_row and token_row.expires_at > datetime.utcnow():
#             return token_row.token

#         # Otherwise generate new token
#         auth_body = {
#             "username": USERNAME,
#             "password": PASSWORD,
#             "access_key": ACCESS_KEY
#         }

#         resp = await self.client.post("/api/login/user", json=auth_body)
#         data = resp.json()

#         if not data.get("success"):
#             raise RuntimeError(f"BigShip Auth Failed: {data}")

#         token = data["data"]["token"]

#         # Save new token
#         await self._save_token(db, token)

#         return token

#     # ================================================================
#     # PRIVATE REQUEST WRAPPER
#     # ================================================================
#     async def _request(self, db: AsyncSession, method: str, url: str, **kwargs):
#         """
#         Handles token, auth header, retries, and rate-limit.
#         """

#         token = await self.get_token(db)

#         headers = kwargs.pop("headers", {})
#         headers["Authorization"] = f"Bearer {token}"
#         headers["Content-Type"] = "application/json"

#         await asyncio.sleep(RATE_LIMIT_SLEEP)

#         resp = await self.client.request(method, url, headers=headers, **kwargs)
#         try:
#             return resp.json()
#         except Exception:
#             return {"success": False, "message": "Invalid JSON from BigShip"}

#     # ================================================================
#     # WAREHOUSE
#     # ================================================================
#     async def add_warehouse(self, db: AsyncSession, payload: dict):
#         return await self._request(db, "POST", "/api/warehouse/add", json=payload)

#     async def get_warehouse_list(self, db: AsyncSession, page_index: int, page_size: int):
#         url = f"/api/warehouse/list?page_index={page_index}&page_size={page_size}"
#         return await self._request(db, "GET", url)

#     # ================================================================
#     # ORDER CREATION
#     # ================================================================
#     async def add_single_order(self, db: AsyncSession, payload: dict):
#         return await self._request(db, "POST", "/api/order/add/single", json=payload)

#     # ================================================================
#     # MANIFEST
#     # ================================================================
#     async def manifest_single(self, db: AsyncSession, payload: dict):
#         """
#         payload = {
#             "system_order_id": int,
#             "courier_id": int,
#             "risk_type": optional
#         }
#         """
#         return await self._request(db, "POST", "/api/order/manifest/single", json=payload)

#     # ================================================================
#     # SHIPMENT DATA (AWB / LABEL / MANIFEST)
#     # ================================================================
#     async def get_shipment_data(self, db: AsyncSession, shipment_data_id: int, system_order_id: int):
#         url = f"/api/shipment/data?shipment_data_id={shipment_data_id}&system_order_id={system_order_id}"
#         return await self._request(db, "GET", url)

#     # ================================================================
#     # CANCEL ORDER
#     # ================================================================
#     async def cancel_awb(self, db: AsyncSession, awb_list: list):
#         payload = {"awbs": awb_list}
#         return await self._request(db, "PUT", "/api/order/cancel", json=payload)

#     # ================================================================
#     # TRACKING
#     # ================================================================
#     async def get_tracking(self, db: AsyncSession, tracking_type: str, tracking_id: str):
#         url = f"/api/tracking?tracking_type={tracking_type}&tracking_id={tracking_id}"
#         return await self._request(db, "GET", url)

#     # ================================================================
#     # CALCULATE RATES (PRE ORDER)
#     # ================================================================
#     async def calculate_rates(self, db: AsyncSession, payload: dict):
#         return await self._request(db, "POST", "/api/order/shipping/rates/calculation", json=payload)

#     # ================================================================
#     # SHIPPING RATES (AFTER ORDER CREATION)
#     # ================================================================
#     async def get_shipping_rates(self, db: AsyncSession, shipment_category: str, system_order_id: int, risk_type: str | None):
#         url = f"/api/order/shipping/rates?shipment_category={shipment_category}&system_order_id={system_order_id}"

#         if risk_type:
#             url += f"&risk_type={risk_type}"

#         return await self._request(db, "GET", url)



# app/microservices/bigship/bigship_client.py
import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.db_base import BigShipToken, OrderShipment  # you already referenced this
from app.utility.logging_utils import log_async  # optional, if you have it
from config.config import settings

# -----------------------------------------
# ENV SETTINGS (required)
# -----------------------------------------
BASE_URL = settings.BASE_URL
USERNAME = settings.USERNAME
PASSWORD = settings.PASSWORD
ACCESS_KEY = settings.ACCESS_KEY
RATE_LIMIT_SLEEP = settings.RATE_LIMIT_SLEEP

if not USERNAME or not PASSWORD or not ACCESS_KEY:
    raise RuntimeError("❌ Missing BigShip environment variables: BIGSHIP_USERNAME/PASSWORD/ACCESS_KEY")

# # Simple rate limit: 100 req/min -> ~0.6s delay
# RATE_LIMIT_SLEEP = float(os.getenv("BIGSHIP_RATE_SLEEP", "0.6"))


class BigShipClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)

    async def close(self):
        await self.client.aclose()

    # -------------------------
    # Token management (DB-backed)
    # -------------------------
    async def _get_saved_token(self, db: AsyncSession) -> Optional[BigShipToken]:
        q = await db.execute(select(BigShipToken).order_by(BigShipToken.id.desc()).limit(1))
        return q.scalars().first()

    async def _save_token(self, db: AsyncSession, token: str):
        obj = BigShipToken(
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        db.add(obj)
        await db.commit()

    async def get_token(self, db: AsyncSession) -> str:
        # return valid token from DB or request new
        token_row = await self._get_saved_token(db)
        if token_row and token_row.expires_at > datetime.utcnow():
            return token_row.token

        auth_body = {
            "user_name": USERNAME,
            "password": PASSWORD,
            "access_key": ACCESS_KEY
        }
        # Note: PDF shows endpoint api/login/user and payload key names may be user_name/password/access_key
        resp = await self.client.post("/api/login/user", json=auth_body)
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError("Invalid JSON received while fetching BigShip token")

        if not data.get("success"):
            raise RuntimeError(f"BigShip Auth Failed: {data}")

        token = data["data"]["token"]
        await self._save_token(db, token)
        return token

    # -------------------------
    # Private request wrapper
    # -------------------------
    async def _request(self, db: AsyncSession, method: str, url: str, **kwargs):
        """
        Handles token injection, rate-limit pause and JSON response normalization.
        """
        token = await self.get_token(db)
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-Type"] = "application/json"
        await asyncio.sleep(RATE_LIMIT_SLEEP)

        resp = await self.client.request(method, url, headers=headers, **kwargs)
        try:
            return resp.json()
        except Exception:
            return {"success": False, "message": "Invalid JSON from BigShip", "status_code": resp.status_code}

    # -------------------------
    # Auth related (exposed)
    # -------------------------
    async def force_refresh_token(self, db: AsyncSession) -> str:
        # clear saved tokens and request a new one immediately
        # If you want you can implement deleting old token rows; for now just request new and save
        # forcing get_token to generate new by saving an expired token is one way; simpler: call login directly
        auth_body = {"user_name": USERNAME, "password": PASSWORD, "access_key": ACCESS_KEY}
        resp = await self.client.post("/api/login/user", json=auth_body)
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError("Invalid JSON from BigShip on force auth")

        if not data.get("success"):
            raise RuntimeError(f"BigShip Auth Failed: {data}")

        token = data["data"]["token"]
        await self._save_token(db, token)
        return token

    # -------------------------
    # Payment category
    # -------------------------
    async def get_payment_category(self, db: AsyncSession, shipment_category: str = "b2c"):
        url = f"/api/payment/category?shipment_category={shipment_category}"
        return await self._request(db, "GET", url)

    # -------------------------
    # Courier list
    # -------------------------
    async def get_courier_list(self, db: AsyncSession, shipment_category: str = "b2c"):
        url = f"/api/courier/get/all?shipment_category={shipment_category}"
        return await self._request(db, "GET", url)

    # -------------------------
    # Wallet balance
    # -------------------------
    async def get_wallet_balance(self, db: AsyncSession):
        return await self._request(db, "GET", "/api/Wallet/balance/get")

    # -------------------------
    # Warehouse
    # -------------------------
    async def add_warehouse(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/warehouse/add", json=payload)

    async def get_warehouse_list(self, db: AsyncSession, page_index: int = 1, page_size: int = 50):
        url = f"/api/warehouse/get/list?page_index={page_index}&page_size={page_size}"
        return await self._request(db, "GET", url)

    # -------------------------
    # Single order
    # -------------------------
    async def add_single_order(self, db: AsyncSession, payload: dict):
        # return await self._request(db, "POST", "/api/order/add/single", json=payload)
        return {
            "success": True,
            "message": "Order created in BigShip",
            "system_order_id": "BSO123456789"
            }


    async def manifest_single(self, db: AsyncSession, payload: dict):
        # return await self._request(db, "POST", "/api/order/manifest/single", json=payload)    
        return {
            "success": True,
            "message": "Order manifested successfully",
            "responseCode": 200
        }

    # -------------------------
    # Heavy order
    # -------------------------
    async def add_heavy_order(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/order/add/heavy", json=payload)

    async def manifest_heavy(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/order/manifest/heavy", json=payload)

    # -------------------------
    # Shipment data (AWB / Label / Manifest)
    # -------------------------
    async def get_shipment_data(self, db: AsyncSession, shipment_data_id: int, system_order_id: int):
        # url = f"/api/shipment/data?shipment_data_id={shipment_data_id}&system_order_id={system_order_id}"
        # return await self._request(db, "GET", url)

        return {
            "success": True,
            "data": {
                "master_awb": "BSAWB123456789",
                "courier_id": 25,
                "courier_name": "Amazon 1Kg",
                "label_url": "https://dummy.bigship.in/label/BSAWB123456789.pdf"
            },
            "message": "Shipment data fetched",
            "responseCode": 200
        }

    # -------------------------
    # Cancel AWB
    # -------------------------
    async def cancel_awb(self, db: AsyncSession, awb_list: list):
        payload = {"awbs": awb_list}
        return await self._request(db, "PUT", "/api/order/cancel", json=payload)

    # -------------------------
    # Tracking
    # -------------------------
    async def get_tracking(self, db: AsyncSession, tracking_type: str, tracking_id: str):
        url = f"/api/tracking?tracking_type={tracking_type}&tracking_id={tracking_id}"
        return await self._request(db, "GET", url)

    # -------------------------
    # Calculator / Rates
    # -------------------------
    async def calculate_rates(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/calculator", json=payload)

    async def get_shipping_rates(self, db: AsyncSession, shipment_category: str, system_order_id: int, risk_type: str | None = None):
        url = f"/api/order/shipping/rates?shipment_category={shipment_category}&system_order_id={system_order_id}"
        if risk_type:
            url += f"&risk_type={risk_type}"
        return await self._request(db, "GET", url)
    
    async def cancel_single_order(self, db: AsyncSession, payload: dict):
        # REAL:
        # return await self._request(db, "POST", "/api/order/cancel", json=payload)

        # DUMMY FOR TESTING
        return {
            "success": True,
            "message": "Order cancelled successfully",
            "responseCode": 200
        }



def calculate_shipment_from_products(order_items):
    total_dead_weight = 0.0
    max_length = 0.0
    max_width = 0.0
    total_height = 0.0

    for item in order_items:
        product = item.product
        qty = item.quantity

        if not all([
            product.weight,
            product.length,
            product.width,
            product.height
        ]):
            raise ValueError(
                f"Missing dimensions for product: {product.product_name}"
            )

        total_dead_weight += float(product.weight) * qty
        max_length = max(max_length, float(product.length))
        max_width = max(max_width, float(product.width))
        total_height += float(product.height) * qty

    # Packing buffer
    max_length += 2
    max_width += 2
    total_height += 2

    volumetric_weight = (
        max_length * max_width * total_height
    ) / 5000

    chargeable_weight = max(total_dead_weight, volumetric_weight)

    return {
        "shipment_weight": round(total_dead_weight, 2),
        "shipment_length": round(max_length, 2),
        "shipment_width": round(max_width, 2),
        "shipment_height": round(total_height, 2),
        "shipment_chargeable_weight": round(chargeable_weight, 2),
    }



async def track_awb(self, db: AsyncSession, awb: str):
    """
    Live tracking using AWB
    """
    # REAL API (enable later)
    # url = f"/api/tracking?tracking_type=awb&tracking_id={awb}"
    # return await self._request(db, "GET", url)

    # ✅ DUMMY RESPONSE (FOR TESTING)
    return {
        "success": True,
        "data": {
            "current_status": "In Transit",
            "last_location": "Mumbai Hub",
            "last_updated": "2025-01-12 18:30",
            "expected_delivery": "2025-01-14"
        }
    }




