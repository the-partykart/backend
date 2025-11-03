from typing import Optional
from fastapi import File, Form, UploadFile
from pydantic import BaseModel

class Createcategory(BaseModel):
    # category_name : str
    # category_image: Optional[str] = "https://images.app.goo.gl/WnqKw3VzGKxk9f7T9"
    category_name: str = Form(...),
    file: Optional[UploadFile] = File(None),

class Updatecategory(BaseModel):
    category_name : Optional[str] = None
    category_image: Optional[str] = None
