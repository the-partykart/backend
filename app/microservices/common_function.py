from decimal import Decimal
from typing import Annotated, Any
from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.inspection import inspect
from datetime import datetime

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from asyncio import log
import configparser
import os
from urllib.parse import urlparse

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db.db_session import get_async_session 
from sqlalchemy.ext.asyncio import AsyncSession 

from app.db.models.db_base import Users
from app.db.services.roles_repository import get_user_role_from_db
from app.utility.logging_utils import log_async, log

from config.config import settings

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from config.config import settings



class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    user_id: int

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), 'config.ini')

config.read(config_file_path)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

GMAIL_USER = settings.GMAIL_USER
GMAIL_APP_PASSWORD = settings.GMAIL_APP_PASSWORD

# Configuration       
cloudinary.config( 
    cloud_name = settings.cloud_name, 
    api_key = settings.api_key, 
    api_secret = settings.api_secret, # Click 'View API Keys' above to copy your API secret
    secure=True
)

from fastapi import BackgroundTasks, Depends, HTTPException 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Annotated
from app.db.services.common_repository import get_user_from_db
from jose import ExpiredSignatureError, JWTError, jwt
from cloudinary.uploader import upload as cloudinary_upload



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")  # Note the leading slash
import os

# async def object_to_dict(obj: Any) -> dict:
#     try:
#         data = {}
#         for column in obj.__table__.columns:
#             value = getattr(obj, column.name)
#             if isinstance(value, datetime):
#                 data[column.name] = value.isoformat()
#             else:
#                 data[column.name] = value
#         return data
#     except Exception as e:
#         # Optionally log the error
#         return {}  # Or raise an exception if preferred


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)], 
        session: AsyncSession= Depends(get_async_session)) -> Users:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        phone_no: str = payload.get("sub")
        # if username is None:
        #     raise credentials_exception
        # In a real application, you would fetch the user from the database based on the username
        user = await get_user_from_db(phone_no=phone_no, session=session)
        if user is None or user == False:
            raise credentials_exception
        
        # data = object_to_dict(user)
        return user
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise credentials_exception
    

# async def object_to_dict(obj):
#     data = {}
#     for c in inspect(obj).mapper.column_attrs:
#         value = getattr(obj, c.key)
#         if isinstance(value, datetime):
#             data[c.key] = value.isoformat()  # Converts datetime to string
#         else:
#             data[c.key] = value
#     return data




async def object_to_dict(obj):
    data = {}
    for c in inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)
        
        # Handle Decimal values
        if isinstance(value, Decimal):
            data[c.key] = float(value)  # Convert Decimal to float (or str, if preferred)
        
        # Handle datetime values
        elif isinstance(value, datetime):
            data[c.key] = value.isoformat()  # Converts datetime to string
        
        # For other types (int, string, etc.), just add them directly
        else:
            data[c.key] = value
    
    return data



# async admin_authorization(

# )

async def get_current_role(
    #     token: Annotated[str, Depends(oauth2_scheme)], 
    #     session: AsyncSession= Depends(get_async_session)) -> Users:
    # credentials_exception = HTTPException(
    #     status_code=401,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    user_id,
    background_tasks: BackgroundTasks, 
    session:AsyncSession,
    ):
    try:
        # payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        # user_id: str = payload.get("user_id")
        
        # if username is None:
        #     raise credentials_exception
        # In a real application, you would fetch the user from the database based on the username
        role = await get_user_role_from_db(
            user_id=user_id, 
            session=session,
            background_tasks=background_tasks
            )
        if role is None or role == False:
            raise HTTPException(
                detail={"message":"Unauthorized User"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        if role.role_id ==1 or role.role_id ==2:
        # data = object_to_dict(user)
            return role
        
        else:
            raise HTTPException(
                detail={"message":"Unauthorized User"},
                status_code=status.HTTP_401_UNAUTHORIZED
            ) 
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized User")
    



async def get_register_user(
    user_id,
    background_tasks: BackgroundTasks, 
    session:AsyncSession,
    ):
    try:
        user = await get_user_from_db(
            user_id=user_id, 
            session=session,
            background_tasks=background_tasks
            )
        if role is None or role == False:
            raise HTTPException(
                detail={"message":"Unauthorized User"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        if role.role_id ==1 or role.role_id ==2:
        # data = object_to_dict(user)
            return role
        
        else:
           raise HTTPException(
                detail={"message":"Unauthorized User"},
                status_code=status.HTTP_401_UNAUTHORIZED
            ) 
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized User")
    




# @app.post("/upload/")
# async def upload_image(file: UploadFile = File(...)):
#     result = cloudinary.uploader.upload(file.file)
#     return {"url": result["secure_url"]}


from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
import uuid
import os

# AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")  # store in .env
AZURE_CONNECTION_STRING = settings.AZURE_STORAGE_CONNECTION_STRING  # store in .env

CONTAINER_NAME = "images" 


async def upload_image(file, background_tasks: BackgroundTasks):
    try:
        # Create async blob service client
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # Generate unique blob name to avoid conflicts
        blob_name = f"{uuid.uuid4()}_{file.filename}"

        # Upload the file
        file_content = await file.read()
        await container_client.upload_blob(
            name=blob_name,
            data=file_content,
            overwrite=True,
            content_settings=ContentSettings(content_type=file.content_type)
        )

        # Construct public URL
        blob_url = f"https://thepartykartstorage.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}"
        return blob_url

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[upload_image] Error uploading to Azure Blob: {e}",
            level="error",
            always_sync=True
        )
        return None
    

# utils/email_templates.py
def build_admin_order_email(order, user, items):
    items_html = "".join(
        f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{i+1}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{item['product_name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{item['quantity']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">₹{float(item['price_per_unit']):,.2f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">₹{float(item['subtotal']):,.2f}</td>
        </tr>
        """ for i, item in enumerate(items)
    )

    return f"""
    <div style="font-family:Arial,sans-serif;color:#333;max-width:700px;margin:auto;background:#fff;border:1px solid #eee;border-radius:10px;overflow:hidden;">
        
        <!-- HEADER -->
        <div style="background-color:#f9f9f9;padding:15px 20px;border-left:6px solid #4CAF50;">
            <h2 style="margin:0;">🛍️ New Order #{order.order_id}</h2>
            <p style="margin:5px 0 0 0;">
                <b>Customer:</b> {getattr(user, 'name', 'N/A')} &nbsp;|&nbsp;
                <b>Phone:</b> {getattr(user, 'phone_no', 'N/A')}
            </p>
        </div>

        <!-- BODY -->
        <div style="padding:20px;">
            <p>Hello Admin,</p>
            <p>A new order has been placed on <b>The PartyKart</b>. Here are the details:</p>

            <!-- ORDER SUMMARY -->
            <h3 style="margin-top:30px;">📦 Order Summary</h3>
            <table style="border-collapse:collapse;width:100%;margin-bottom:20px;font-size:14px;">
                <thead>
                    <tr style="background-color:#f4f4f4;">
                        <th style="padding:8px;border:1px solid #ddd;">#</th>
                        <th style="padding:8px;border:1px solid #ddd;">Product</th>
                        <th style="padding:8px;border:1px solid #ddd;">Qty</th>
                        <th style="padding:8px;border:1px solid #ddd;">Price</th>
                        <th style="padding:8px;border:1px solid #ddd;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>{items_html}</tbody>
            </table>

            <p style="font-size:15px;margin-top:10px;">
                <b>Total:</b> ₹{float(order.total_amount):,.2f}<br>
                <b>Final Amount:</b> ₹{float(order.final_amount):,.2f}
            </p>

            <!-- DELIVERY DETAILS -->
            <h3 style="margin-top:30px;">🚚 Delivery Details</h3>
            <div style="background:#fafafa;padding:15px;border:1px solid #eee;border-radius:8px;line-height:1.6;">
                <b>Name:</b> {getattr(user, 'name', 'N/A')}<br>
                <b>Phone:</b> {getattr(user, 'phone_no', 'N/A')}<br>
                <b>Address:</b> {order.shipping_address}<br>
                <b>Payment:</b> {order.payment_method} ({order.payment_status})<br>
                <b>Delivery Status:</b> {order.delivery_status}
            </div>

            <p style="font-size:13px;color:#555;margin-top:15px;">
                <i>Order Date:</i> {order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else 'N/A'}
            </p>

            <!-- FOOTER -->
            <div style="border-top:1px solid #eee;margin-top:30px;padding-top:15px;text-align:center;">
                <p style="margin:0;font-size:14px;">Regards,<br><b>The PartyKart</b> 🎉</p>
                <p style="margin:5px 0 0 0;font-size:12px;color:#888;">This is an automated order notification email.</p>
            </div>
        </div>
    </div>
    """



import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# async def send_admin_notification_async(from_email: str, app_password: str, to_email: str, subject: str, html_body: str):
#     """
#     Asynchronously sends an order notification email to the admin.
#     """
#     try:
#         message = MIMEMultipart("alternative")
#         message["From"] = from_email
#         message["To"] = to_email
#         message["Subject"] = subject
#         message.attach(MIMEText(html_body, "html"))

#         await aiosmtplib.send(
#             message,
#             hostname="smtp.gmail.com",
#             port=587,
#             start_tls=True,
#             username=from_email,
#             password=app_password,
#         )
#         print(f"✅ [MAIL] Admin notification sent to {to_email}")

#     except Exception as e:
#         print(f"⚠️ [MAIL ERROR] Failed to send admin email: {e}")


async def send_admin_notification_async(from_email, app_password, to_emails, subject, html_body):
    if isinstance(to_emails, str):
        to_emails = [to_emails]  # allow both single or multiple

    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=from_email,
            password=app_password,
            recipients=to_emails,  # ✅ sends to all
        )
        log.info(f"✅ Admin notification sent to {', '.join(to_emails)}")
    except Exception as e:
        log.info(f"❌ Error sending admin notification: {e}")