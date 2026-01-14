from dataclasses import dataclass
from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    description: str
    hsn: str
    quantity: float
    rate: float
    per: str

# class InvoiceRequest(BaseModel):
#     buyer_name: str
#     bill_no: str
#     challan_no: str
#     date: str
#     vehicle_no: str
#     place_of_delivery: str
#     loading_charge: float
#     products: List[Product]


@dataclass
class BillSummary:
    final_amount: float
    GST_amount: float
    total_amount : float


class InvoiceRequest(BaseModel):
    buyer_name: str
    buyer_address: str   # ✅ NEW (FULL TEXT)
    bill_no: str
    challan_no: str
    date: str
    vehicle_no: str
    place_of_delivery: str
    loading_charge: Optional[float] = 0
    products: List[Product]
