from typing import Optional
from fastapi import File, Form, UploadFile
from pydantic import BaseModel

class Createcart(BaseModel):
    # cart_name : str
    # cart_image: Optional[str] = "https://images.app.goo.gl/WnqKw3VzGKxk9f7T9"
    cart_name: str = Form(...),
    file: Optional[UploadFile] = File(None),

class Updatecart(BaseModel):
    cart_name : Optional[str] = None
    cart_image: Optional[str] = None
