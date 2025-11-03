from pydantic import BaseModel, HttpUrl
from typing import Optional

class CreateProduct(BaseModel):
    product_name : str
    product_price : int
    product_description : Optional[str] = "No information available for this product"
    category_id : Optional[int] = None
    # product_image: Optional[str] = "https://images.app.goo.gl/WnqKw3VzGKxk9f7T9"

class Updateproduct(BaseModel):
    product_name : Optional[str] = None
    product_price : Optional[int] = None
    product_description : Optional[str] = "No information available for this product"
    product_image: Optional[str] = None


from pydantic import BaseModel, HttpUrl
from typing import Optional

class CourseCreate(BaseModel):
    course_name: str
    course_link: HttpUrl   # ensures it's a valid link


class CourseResponse(BaseModel):
    course_id: int
    course_name: str
    course_link: str
    created_by: Optional[int]

    class Config:
        from_attributes = True   # ✅ Pydantic v2 style
