from typing import Any, List, Optional
from pydantic import BaseModel, Field



class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    offer_id: Optional[int] = None
    promocode_id: Optional[int] = None


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    payment_method: str
    shipping_address: Any