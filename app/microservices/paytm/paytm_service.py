import uuid

def create_paytm_txn(order_id: str, amount: float, customer_id: str):
    # Dummy response (like Paytm INITIATE TXN API)
    return {
        "mid": "DUMMY_MID",
        "orderId": order_id,
        "txnToken": str(uuid.uuid4()),
        "amount": amount,
        "callbackUrl": "http://localhost:8000/api/paytm/callback"
    }

def verify_paytm_callback(data: dict):
    # Dummy verification logic
    if data.get("STATUS") == "TXN_SUCCESS":
        return True
    return False


import os
import uuid
from config.config import settings
from app.microservices.paytm.paytm_checksum import generate_checksum


MID = settings.PAYTM_MID
KEY = settings.PAYTM_MERCHANT_KEY
CALLBACK_URL = settings.PAYTM_CALLBACK_URL
FORCE_SUCCESS = settings.PAYTM_FORCE_SUCCESS

def initiate_paytm_transaction(order_id: str, amount: float, customer_id: str):
    body = {
        "requestType": "Payment",
        "mid": MID,
        "websiteName": os.getenv("PAYTM_WEBSITE"),
        "orderId": order_id,
        "callbackUrl": CALLBACK_URL,
        "txnAmount": {
            "value": f"{amount:.2f}",
            "currency": "INR"
        },
        "userInfo": {
            "custId": customer_id
        }
    }

    checksum = generate_checksum(body, KEY)

    # 🔥 LOCAL FORCE SUCCESS (NO PAYTM HIT)
    if FORCE_SUCCESS:
        return {
            "txnToken": str(uuid.uuid4()),
            "orderId": order_id,
            "amount": amount,
            "mock": True
        }

    # 🔁 REAL PAYTM API (enable later)
    # POST https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction

    raise NotImplementedError("Enable Paytm API call later")
