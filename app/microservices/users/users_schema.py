from typing import Optional
from pydantic import BaseModel

class Login(BaseModel):
    phone_no : str
    password : str

class UserCreate(BaseModel):
    phone_no: str 
    name : Optional[str] = None 
    email : Optional[str] = None
    phone_no : Optional[str] = None
    business_name : Optional[str] = None
    password : str 
    role :int = 3

class UpdateUserDetails(BaseModel):
    name : str