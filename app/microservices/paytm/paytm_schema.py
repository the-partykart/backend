from pydantic import BaseModel

class CreatePaymentRequest(BaseModel):
    order_id: str
    amount: float
    customer_id: str

class PaytmCallbackResponse(BaseModel):
    ORDERID: str
    STATUS: str
    TXNID: str | None = None
