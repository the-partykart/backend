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
from sqlalchemy import delete, select

from app.db.models.db_base import BigShipToken, OrderShipment  # you already referenced this
from app.utility.logging_utils import log_async, log # optional, if you have it
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
        self.base_url = settings.BASE_URL
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)

    async def close(self):
        await self.client.aclose()

    # -------------------------
    # Token management (DB-backed)
    # -------------------------
    async def _get_saved_token(self, db: AsyncSession) -> Optional[BigShipToken]:
        q = await db.execute(select(BigShipToken).order_by(BigShipToken.id.desc()).limit(1))
        return q.scalars().first()

    # async def _save_token(self, db: AsyncSession, token: str):
    #     obj = BigShipToken(
    #         token=token,
    #         expires_at=datetime.utcnow() + timedelta(hours=12)
    #     )
    #     db.add(obj)
    #     await db.commit()

    async def _save_token(self, db: AsyncSession, token: str):
        await db.execute(delete(BigShipToken))
        db.add(BigShipToken(
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        ))
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
    # async def _request(self, db: AsyncSession, method: str, url: str, **kwargs):
    #     """
    #     Handles token injection, rate-limit pause and JSON response normalization.
    #     """
    #     token = await self.get_token(db)
    #     headers = kwargs.pop("headers", {})
    #     headers["Authorization"] = f"Bearer {token}"
    #     headers["Content-Type"] = "application/json"
    #     await asyncio.sleep(RATE_LIMIT_SLEEP)

    #     resp = await self.client.request(method, url, headers=headers, **kwargs)
    #     try:
    #         return resp.json()
    #     except Exception:
    #         return {"success": False, "message": "Invalid JSON from BigShip", "status_code": resp.status_code}

    # async def _request(self, db: AsyncSession, method: str, url: str, json=None):
    #     token = await self.get_token(db)

    #     headers = {
    #         "Authorization": f"Bearer {token}",
    #         "Content-Type": "application/json"
    #     }

    #     async with httpx.AsyncClient(base_url=self.base_url) as client:
    #         response = await client.request(method, url, json=json, headers=headers)

    #         # 🔁 TOKEN EXPIRED → RELogin
    #         if response.status_code in (401, 403):
    #             await self.force_refresh_token(db)

    #             token = await self.get_token(db)
    #             headers["Authorization"] = f"Bearer {token}"

    #             response = await client.request(
    #                 method, url, json=json, headers=headers
    #             )

    #         response.raise_for_status()
    #         return response.json()

    async def _request(self, db: AsyncSession, method: str, url: str, json=None):
        token = await self.get_token(db)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.request(method, url, json=json, headers=headers)

            # 🔁 Retry on auth failure
            if response.status_code in (401, 403):
                await self.force_refresh_token(db)
                token = await self.get_token(db)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.request(method, url, json=json, headers=headers)

            # 🔴 LOG ACTUAL BIGSHIP ERROR
            if response.status_code >= 400:
                try:
                    print("BIGSHIP ERROR:", response.json())
                except Exception:
                    print("BIGSHIP ERROR RAW:", response.text)

                raise RuntimeError(
                    f"BigShip API Error {response.status_code}: {response.text}"
                )

            return response.json()


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
    # async def add_single_order(self, db: AsyncSession, payload: dict):
    #     # return await self._request(db, "POST", "/api/order/add/single", json=payload)
    #     # return {
    #     #     "success": True,
    #     #     "message": "Order created in BigShip",
    #     #     "system_order_id": "BSO123456789"
    #     #     }

    #     # Make the actual HTTP POST request
    #     response = await self._request(
    #         db,
    #         method="POST",
    #         endpoint="/api/order/add/single",
    #         json=payload
    #     )

    #     return response

    # async def add_single_order(self, db: AsyncSession, payload: dict):
    #     return await self._request(
    #         db,
    #         "POST",
    #         "/api/order/add/single",
    #         json=payload
    #     )

    async def add_single_order(self, db: AsyncSession, payload: dict):
        try:
            return await self._request(
                db=db,
                method="POST",
                url="/api/order/add/single",
                json=payload
            )
        except httpx.HTTPStatusError as e:
            try:
                data = e.response.json()
            except Exception:
                data = {"message": e.response.text}

            log.error("BIGSHIP ERROR:", data)
            raise RuntimeError(f"BigShip Order Failed: {data}")


    async def manifest_single(self, db: AsyncSession, payload: dict):
        # return await self._request(db, "POST", "/api/order/manifest/single", json=payload)    
        # return {
        #     "success": True,
        #     "message": "Order manifested successfully",
        #     "responseCode": 200
        # }

        return await self._request(
            db=db,
            method="POST",
            url="/api/order/manifest/single",
            json=payload
        )

    # -------------------------
    # Heavy order
    # -------------------------
    async def add_heavy_order(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/order/add/heavy", json=payload)

    async def manifest_heavy(self, db: AsyncSession, payload: dict):
        return await self._request(db, "POST", "/api/order/manifest/heavy", json=payload)


    async def get_shipment_data(
        self,
        db: AsyncSession,
        shipment_data_id: int,
        system_order_id: int
    ):
        """
        BigShip: POST request with QUERY PARAMS (no body)
        """
        url = (
            f"/api/shipment/data"
            f"?shipment_data_id={shipment_data_id}"
            f"&system_order_id={system_order_id}"
        )

        return await self._request(
            db=db,
            method="POST",
            url=url,
            json=None  
        )
    
    async def get_tracking_details(
        self,
        db: AsyncSession,
        tracking_type: str,
        tracking_id: str
    ):
        """
        Get tracking details using AWB or LRN
        """
        url = (
            f"/api/tracking"
            f"?tracking_type={tracking_type}"
            f"&tracking_id={tracking_id}"
        )

        return await self._request(
            db=db,
            method="GET",
            url=url
        )




    # -------------------------
    # Cancel AWB
    # -------------------------
    async def cancel_awb(self, db: AsyncSession, awbs: list[str]):
        return await self._request(
            db=db,
            method="PUT",
            url="/api/order/cancel",
            json=awbs
        )


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


from decimal import Decimal

PACKING_BUFFER_CM = 2
VOLUMETRIC_DIVISOR = 5000  # BigShip standard


def calculate_shipment_from_products(order_items):
    if not order_items:
        raise ValueError("No order items found")

    total_dead_weight = Decimal("0.0")
    max_length = Decimal("0.0")
    max_width = Decimal("0.0")
    total_height = Decimal("0.0")

    breakdown = []

    for item in order_items:
        product = item.product
        qty = item.quantity

        if not product:
            raise ValueError("Product missing in order item")

        if qty <= 0:
            raise ValueError(f"Invalid quantity for {product.product_name}")

        if not all([
            product.weight,
            product.length,
            product.width,
            product.height
        ]):
            raise ValueError(
                f"Missing dimensions for product: {product.product_name}"
            )

        weight = Decimal(product.weight)
        length = Decimal(product.length)
        width = Decimal(product.width)
        height = Decimal(product.height)

        total_dead_weight += weight * qty
        max_length = max(max_length, length)
        max_width = max(max_width, width)
        total_height += height * qty

        breakdown.append({
            "product": product.product_name,
            "qty": qty,
            "weight": float(weight),
            "dimensions": f"{length}x{width}x{height}"
        })

    # 📦 Packing buffer
    max_length += PACKING_BUFFER_CM
    max_width += PACKING_BUFFER_CM
    total_height += PACKING_BUFFER_CM

    volumetric_weight = (
        max_length * max_width * total_height
    ) / Decimal(VOLUMETRIC_DIVISOR)

    chargeable_weight = max(total_dead_weight, volumetric_weight)

    return {
        "shipment_weight": float(total_dead_weight.quantize(Decimal("0.01"))),
        "shipment_length": float(max_length.quantize(Decimal("0.01"))),
        "shipment_width": float(max_width.quantize(Decimal("0.01"))),
        "shipment_height": float(total_height.quantize(Decimal("0.01"))),
        "shipment_chargeable_weight": float(chargeable_weight.quantize(Decimal("0.01"))),
        "calculation_meta": {
            "volumetric_divisor": VOLUMETRIC_DIVISOR,
            "packing_buffer_cm": PACKING_BUFFER_CM,
            "items": breakdown
        }
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





