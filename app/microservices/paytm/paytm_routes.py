from fastapi import APIRouter
from app.microservices.paytm.paytm_schema import CreatePaymentRequest, PaytmCallbackResponse
from app.microservices.paytm.paytm_service import create_paytm_txn, verify_paytm_callback

router = APIRouter(prefix="/api/paytm", tags=["Paytm"])

@router.post("/create-order")
async def create_order(payload: CreatePaymentRequest):
    txn_data = create_paytm_txn(
        payload.order_id,
        payload.amount,
        payload.customer_id
    )

    return {
        "success": True,
        "paytm": txn_data
    }

from fastapi import APIRouter, Request
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter(prefix="/api/paytm")

@router.post("/callback")
async def paytm_callback(request: Request):
    data = await request.json()

    if os.getenv("PAYTM_FORCE_SUCCESS") == "true":
        return {
            "status": "PAID",
            "order_id": data.get("ORDERID"),
            "verified": True,
            "mock": True
        }

    # 🔐 REAL VERIFICATION (enable later)
    # 1. Extract CHECKSUMHASH
    # 2. Verify checksum
    # 3. Check STATUS == TXN_SUCCESS

    return {"status": "FAILED"}
