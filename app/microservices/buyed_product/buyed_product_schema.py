from typing import List, Optional
from pydantic import BaseModel, Field

class ProductCategoryList(BaseModel):
    product_id: int = Field(..., alias="product_id")
    # category_id: int = Field(..., alias="category_id")
    offer_id: Optional[int] = Field(None, alias="offer_id")
    quantity: Optional[int] = Field(1, alias="quantity")
    promocode_id: Optional[int] = Field(None, alias="promocode_id")
    shipping_address : Optional[str] = Field(None)
    payment_method : Optional[str] = Field(None)
    payment_status : Optional[str] = Field(None)
    shipping_details : Optional[dict] = Field(None),





class Updateproduct(BaseModel):
    product_name : Optional[str] = None
    product_price : Optional[int] = None
    product_description : Optional[str] = "No information available for this product"

class CartProductData(BaseModel):
    product_id : Optional[int] = None
    product_quantity : Optional[int] = None

class CartProductOfferData(BaseModel):
    offer_id : Optional[int] = None,
    promocode_id : Optional[int] = None,