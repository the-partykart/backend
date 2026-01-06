# app/microservices/bigship/bigship_schema.py
from pydantic import BaseModel, Field
from pydantic.types import StringConstraints
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime

PincodeStr = Annotated[str, StringConstraints(min_length=6, max_length=6, strip_whitespace=True)]
PhoneStr = Annotated[str, StringConstraints(min_length=10, max_length=12, strip_whitespace=True)]
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class TokenResponse(BaseModel):
    token: str
    expires_at: datetime

class WarehouseAdd(BaseModel):
    address_line1: Annotated[str, StringConstraints(min_length=10, max_length=50)]
    address_line2: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    address_landmark: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    address_pincode: PincodeStr
    contact_number_primary: PhoneStr

class AWBRequest(BaseModel):
    shipment_data_id: int
    system_order_id: int

class CancelPayload(BaseModel):
    awbs: List[NonEmptyStr]

class ManifestPayload(BaseModel):
    system_order_id: int
    courier_id: Optional[int] = None
    risk_type: Optional[str] = None

# A minimal but practical AddSingleOrderPayload & CalculateRates to satisfy API
class ProductDetail(BaseModel):
    product_category: NonEmptyStr
    product_sub_category: Optional[str] = None
    product_name: NonEmptyStr
    product_quantity: int
    each_product_invoice_amount: float
    each_product_collectable_amount: Optional[float] = 0.0
    hsn: Optional[str] = ""

class BoxDetail(BaseModel):
    each_box_dead_weight: float
    each_box_length: int
    each_box_width: int
    each_box_height: int
    each_box_invoice_amount: float
    each_box_collectable_amount: Optional[float] = 0.0
    box_count: int
    product_details: List[ProductDetail]

class ConsigneeAddress(BaseModel):
    address_line1: NonEmptyStr
    address_line2: Optional[str] = ""
    address_landmark: Optional[str] = ""
    pincode: PincodeStr

class ConsigneeDetail(BaseModel):
    first_name: NonEmptyStr
    last_name: NonEmptyStr
    company_name: Optional[str] = ""
    contact_number_primary: PhoneStr
    contact_number_secondary: Optional[PhoneStr] = None
    email_id: Optional[str] = ""
    consignee_address: ConsigneeAddress

class WarehouseDetail(BaseModel):
    pickup_location_id: int
    return_location_id: int

class OrderDetail(BaseModel):
    invoice_date: datetime
    invoice_id: NonEmptyStr
    payment_type: NonEmptyStr
    shipment_invoice_amount: float
    total_collectable_amount: Optional[float] = 0.0
    box_details: List[BoxDetail]
    ewaybill_number: Optional[str] = ""
    document_detail: Optional[Dict[str, Any]] = {}

class AddSingleOrderPayload(BaseModel):
    shipment_category: NonEmptyStr = "b2c"
    warehouse_detail: WarehouseDetail
    consignee_detail: ConsigneeDetail
    order_detail: OrderDetail

class CalculateRatesPayload(BaseModel):
    shipment_category: NonEmptyStr
    payment_type: NonEmptyStr
    pickup_pincode: int = 410206
    destination_pincode: int
    shipment_invoice_amount: float
    risk_type: Optional[str] = ""
    box_details: List[BoxDetail]

class TrackingQuery(BaseModel):
    tracking_type: NonEmptyStr
    tracking_id: NonEmptyStr

class CreateShipmentPayload(BaseModel):
    shipment_weight: float = Field(..., gt=0)
    shipment_length: float = Field(..., gt=0)
    shipment_width: float = Field(..., gt=0)
    shipment_height: float = Field(..., gt=0)
    shipment_chargeable_weight: float = Field(..., gt=0)

    # Optional (store rate API response for audit)
    rate_response: Optional[Dict] = None