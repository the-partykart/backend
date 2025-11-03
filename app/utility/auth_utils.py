from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from jose import jwt
from fastapi import HTTPException
from config.config import settings
from app.utility.logging_utils import log, log_async

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes 


async def create_access_token(
    data : dict,
    user_id: int,
    phone_no: str,
    role_id: int,
    role_name: str,
    expires_delta : timedelta = None
):
    try:
        to_encode = data
        expire = None
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
        response = {
            "token": encoded_jwt,
            "token_type": "Bearer",
            "expires_in": expire,
            "user": {
                "id": user_id,
                "phone_no": phone_no,
                "role": role_id,
                "role name": role_name
            }
        }
        return response
    
    except Exception as e:
        log.error("Error in creating access token.")
        raise HTTPException(status_code = 401, detail = f"Error in creating access token.")
    
async def hashed_password(password:str):
    '''
    This function convert normal password into hashed password and return it.
    '''
    try:
        hashed = pwd_context.hash(password)
        return hashed
    
    except Exception as e:
        log.error(f"Error in Hashed passwoed: {e}")
        return None
    
async def verify_passwords(plain_password: str, hashed_password: str) -> bool:
    '''
    Verifies the entered password against the hashed password.
    Returns True if they match, otherwise False.
    '''
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error verifying password: {e}")
    
    
async def generate_password_from_number(phone_number: str) -> str:
    try:
        if not phone_number.isdigit() or len(phone_number) != 10:
            raise ValueError("Phone number must be a 10-digit number")

        first_part = phone_number[:5]
        second_part = phone_number[5:]
        password = f"pass{first_part}word{second_part}"
        return password
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error verifying password: {e}")