# '''
# All user related CRUD operations
# '''

import asyncio
import os
import shutil
import tempfile
from types import SimpleNamespace
from urllib.parse import quote_plus
from fastapi import FastAPI, Depends, BackgroundTasks, File, Form, UploadFile, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
import sys
from sqlalchemy import create_engine
import uvicorn

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session, get_async_session_context
from app.db.models.db_base import Users
from app.db.services.roles_repository import check_roles, check_superadmin, master_role
from app.db.services.users_repository import  check_phone_no_db, get_user_by_id_db
from app.microservices.common_function import User, get_current_role, get_current_user, object_to_dict
from app.microservices.users.marg_sync_service import run_marg_sync_job, sync_products_from_marg_excel
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.microservices.users.users_service import check_phone_no_service, check_username_service, create_user_logic, delete_user_service, fetch_all_information_service, fetch_all_users_service, update_user_service
from app.utility.auth_utils import create_access_token, generate_password_from_number, verify_passwords
from app.utility.logging_utils import log_async, log_background 
from config.config import settings

global_prefix = settings.global_prefix

app = FastAPI()
router_v1 = APIRouter(prefix=f"/{global_prefix}/user")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# origins = [
#     "http://localhost:8081",  # frontend port
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],       # or ["*"] for all origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@router_v1.post("/auth/login")
async def login_handler(
    data: Login,
    background_tasks : BackgroundTasks,
    session : AsyncSession = Depends(get_async_session),
):
    try:
        valid_phone_no = await check_phone_no_service(
            phone_no=data.phone_no,
            session=session,
            background_tasks=background_tasks,
        )
        if not valid_phone_no:
            raise HTTPException(status_code=404, detail="Phone Number not registered")
        
        
        phone_no = valid_phone_no[0]["user"].get("phone_no")
        hash_pass = valid_phone_no[0]["user"].get("password")
        user_id = valid_phone_no[0]["user"].get("user_id")
        role_name = valid_phone_no[0]["role"].get("role_name")
        user_role = valid_phone_no[0]["user_role"].get("role_id")


        result = await verify_passwords(data.password, hashed_password=hash_pass)
        if not result:
            return HTTPException(detail="Invalid password", status_code=401)
        
        data = {
            "sub" : phone_no,
            "user_id": user_id,
            "role":user_role
        }
        token_result = await create_access_token(
            data=data, 
            user_id=user_id,
            phone_no=phone_no,
            role_id=user_role,
            role_name=role_name,
            expires_delta=timedelta(hours=12)
            )

        return token_result

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[USERS][Login] Error: Failed to login. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Error in login")
    
    
@app.post("/master-users")
async def create_master_user_handler(
    background_tasks :BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
    # user: Users = Depends(get_current_user)
):
    try:
        role_result = await check_roles(session=session)
        if role_result:
            current_role = role_result.role_id
        if not role_result or role_result == None:
            role_insertion_result = await master_role(session=session)
            if not role_insertion_result:
                raise HTTPException(detail="Unable to insert master_role")
            current_role = role_insertion_result

        user_result = await check_superadmin(session=session)
        if user_result is None or user_result == False:
            master_data = {
                "name" :  "master admin",
                "email" :  "admin@sample.com",
                "phone_no": "8779319669",
                "business_name": "master admin",
                "password" :  "Password@123",
                "role" : current_role 
            }

            data = SimpleNamespace(**master_data)
            result = await create_user_logic(
                session=session, 
                data=data,
                background_tasks=background_tasks,
                user_id=0)
            if result["status"] == "success":
                # log.info(f"User: {data.name}, username: {data.email} created successfully ")
                log_async(
                    background_tasks=background_tasks,
                    message=f"[USERS][MASTER_USER] Error: Failed to create master user. Exception: {e}",
                    level="info",
                )
                return JSONResponse(content="User created successfully", status_code=201)
            else:
                return JSONResponse(content="User creation failed", status_code=404)
    
        if user_result:
            return JSONResponse(content="Master data already inserted", status_code=201)
        
    except Exception as e:
        return JSONResponse(content="Master data already inserted", status_code=201)
    

@router_v1.post("/register")
async def register_user_handler(
    data: UserCreate, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    # user: Users = Depends(get_current_user),
):
    try:
        user_id=1
        check_phone_no_exists = await check_phone_no_db(
            phone_no=data.phone_no,
            session=session,
            background_tasks=background_tasks,
        )
        if check_phone_no_exists:
            # log_async(
            #     background_tasks,
            #     f"[API][CREATE_USER][EMAIL_CHECK] Attempted to create user with existing email: {data.email}.",
            #     "info"
            # )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone Number is already registered. Please use a different Phone number.."
            )

        result = await create_user_logic(
            background_tasks=background_tasks,
            session=session, 
            data=data, 
            user_id=user_id
            )
        
        if result:
            # log.info(f"User: {data.name}, username: {data.email} created successfully ")
            log_async(
                    background_tasks=background_tasks,
                    message=f"[USERS][CREATE_USER] Success: User Register Successfully",
                    level="info",
                )
            return JSONResponse(content={
                "status": 1 , 
                "message":"User Register successfully"},
                status_code=201)
        else:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User Registration failed"
        )
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        log_async(
                    background_tasks=background_tasks,
                    message=f"[API][CREATE_USER] Unexpected error during user registration for no. {data.phone_no}: {e}",
                    level="error",
                    always_sync=True,
                )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred during user registration."
        )
    
    
@router_v1.get("/{user_id}")
async def get_user_by_id_handler(
    user_id:int,
    background_tasks : BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),
    # user = Users(user_id=1)
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        check_user_id = await get_user_by_id_db(
            user_id=user_id, 
            background_tasks=background_tasks,
            session=session,
            )
        if check_user_id is None or check_user_id==False:
            raise HTTPException(detail="Invalide user_id", status_code=404)
        data = await object_to_dict(check_user_id)

        return JSONResponse(content={
            "status" : 1,
            "data" : data
        },
        status_code=200)
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        log_async(
            background_tasks,
            f"[USER_FETCH] Error: Failed to get user with user_id={user_id}. Exception: {e}",
            "error",
            always_sync=True
        )
        raise HTTPException(status_code=404, detail="Error in get all users")
    
@router_v1.get("/users")
async def get_all_users_handler(
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user)
    ):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )
        
        result = await fetch_all_users_service(
            background_tasks=background_tasks,
            session=session
            )
        if result["status"] == 1:
            return result
        
    except HTTPException as http_exc:
        raise http_exc
        
    except Exception as e:
        background_tasks.add_task(log_background,"error in get user","error")
        raise HTTPException(status_code=404, detail="Error in get all users")

    
@router_v1.patch("/update_user/{u_user_id}",status_code=status.HTTP_200_OK)
async def update_user_handler(
    data: UpdateUserDetails,
    u_user_id : int,
    background_tasks : BackgroundTasks,
    user : Users = Depends(get_current_user),
    # user= Users(user_id=1),
    session: AsyncSession = Depends(get_async_session),
    ):
    try:
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        user_id = user.user_id
        check_user_id = await get_user_by_id_db(
            user_id=u_user_id, 
            background_tasks=background_tasks,
            session=session,
            )
        if not check_user_id: 
            log_async(
                background_tasks,
                f"[API][UPDATE_USER] User with ID {u_user_id} not found.",
                "warning"
            )
            
            raise HTTPException(
                detail="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        current_name = check_user_id.name
        result = await update_user_service(
            user_id = user_id,
            current_name = current_name,
            background_tasks = background_tasks,
            session=session, 
            data=data,
            u_user_id=u_user_id,
            )
        if result:
            log_async(
                background_tasks,
                f"[API][UPDATE_USER] User with ID {user_id} updated successfully.",
                "info"
            )
            return {"message": "User updated successfully."}
        else:
            log_async(
                background_tasks,
                f"[API][UPDATE_USER] Failed to update user with ID {user_id} after service call.",
                "error",
                always_sync=True 
            )
            raise HTTPException(
                detail="Failed to update user details.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR # Or 400 if it's a client data issue
            )


    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        log_async(
            background_tasks,
            f"[API][UPDATE_USER] Unexpected error while updating user {user_id}: {str(e)}",
            "error",
            always_sync=True
        )
        raise HTTPException(
            detail="An unexpected error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@router_v1.put("/delete_user/{target_user_id}")
async def soft_delete_user_handler(
    target_user_id : int,
    background_tasks: BackgroundTasks,
    session: AsyncSession= Depends(get_async_session),
    user: Users = Depends(get_current_user),
    ):
    try:
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        user_id = User.user_id
        deleted_result = await get_user_by_id_db(
            user_id = target_user_id,
            session=session,
            background_tasks=background_tasks,
        )
        if not deleted_result:
            log_async(
                background_tasks,
                f"[API][DELETE_USER] Attempted soft-delete for non-existent user ID: {target_user_id}.",
                "info",
                always_sync=True
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found."
            )
        if deleted_result.is_deleted:
            log_async(
                background_tasks,
                f"[API][DELETE_USER] User {target_user_id} is already marked as deleted.",
                "info",
                always_sync=True
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with ID {target_user_id} is already deleted."
            )
        if target_user_id == user_id:
            log_async(
                background_tasks,
                f"[API][DELETE_USER] Self Deletion Not Allow",
                "info" ,
                always_sync=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Self Deletion Not Allow"
            )
        result = await delete_user_service(
            target_user_id,
            user_id,
            background_tasks=background_tasks, 
            session=session)
        if result and result.get("status") == "success":
            log_async(
                background_tasks,
                f"[API][DELETE_USER] User {target_user_id} soft-deleted successfully by user {user_id}.",
                "info"
            )
            return JSONResponse(
                content={"message": result.get("message")},
                status_code=status.HTTP_200_OK # Or HTTP_204_NO_CONTENT if no content
            )
        elif result and result.get("status") == "not_found":
            log_async(
                background_tasks,
                f"[API][DELETE_USER] Soft-delete failed for user {target_user_id}: User not found by service.",
                "info",
                always_sync=True
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message")
            )
        else: # Catches "error" or unexpected results from service
            log_async(
                background_tasks,
                f"[API][DELETE_USER] Soft-delete failed for user {target_user_id} due to service error. Result: {result}",
                "error"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "An internal server error occurred during soft-deletion.")
            )

    except HTTPException as http_exc:
    # Re-raise explicit HTTPExceptions to be caught by FastAPI
        raise http_exc
    
    except Exception as e:
        log_async( # Use log_async here
            background_tasks,
            f"[API][DELETE_USER] Unexpected error during soft-deletion of user {target_user_id}: {str(e)}",
            "error",
            exc_info=True # Crucial for debugging unexpected errors
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred."
        )

@router_v1.get("/information/")
async def check_all_information_db(
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_async_session),
    ):
    try:
        
        result = await fetch_all_information_service(
            background_tasks=background_tasks,
            session=session
            )
        
        # if result:
        return result
        
    except HTTPException as http_exc:
        raise http_exc
        
    except Exception as e:
        background_tasks.add_task(log_background,"error in get information","error")
        raise HTTPException(status_code=404, detail="Error in get all information")












from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from urllib.parse import quote_plus
from config.config import settings

# ✅ Database configuration (from .env / settings)
db_name = settings.db_name
db_drivername = settings.db_drivername  # usually 'asyncmy'
db_username = settings.db_username
db_password = settings.db_password
db_port = settings.db_port
db_database_name = settings.db_database_name
db_server = settings.db_server

print("Driver:", db_drivername)
print("User:", db_username)
print("Password:", db_password)
print("Host:", db_server)
print("Port:", db_port)
print("DB:", db_database_name)



# ✅ Build the async MySQL connection URL
DB_URL = f"mysql+{db_drivername}://{db_username}:{db_password}@{db_server}:{db_port}/{db_database_name}"


print("FINAL URL:", DB_URL)


# DB_URL = "mysql+asyncmy://root:root@localhost:3306/pk"


# ✅ Create async engine with connection pooling
async_engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=600,   # Recycle connections every 10 min
    pool_pre_ping=True,
    future=True
)

from sqlalchemy.orm import sessionmaker, Session


# @router_v1.post("/data-dump")
# async def data_dump(
#     file: UploadFile = File(...),
#     sync_password: str = Form(...),
# ):
    
#     engine = create_engine(DB_URL, pool_pre_ping=True)

#     SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


#     def get_db() -> Session:
#         db = SessionLocal()
#         try:
#             yield db
#         finally:
#             db.close()


#     if not file.filename:
#         raise HTTPException(status_code=400, detail="File missing")

#     if not file.filename.lower().endswith((".xls", ".xlsx")):
#         raise HTTPException(status_code=400, detail="Invalid Excel file")

#     temp_dir = tempfile.mkdtemp()
#     file_path = os.path.join(temp_dir, file.filename)

#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         result = sync_products_from_marg_excel(
#             db=db,
#             file_path=file_path,
#             sync_password=sync_password,
#             system_user_id=None
#         )

#         return {
#             "status": "success",
#             "message": "Marg data synced successfully",
#             "result": result
#         }

#     except PermissionError as e:
#         raise HTTPException(status_code=401, detail=str(e))

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         try:
#             file.file.close()
#             os.remove(file_path)
#             os.rmdir(temp_dir)
#         except Exception:
#             pass

import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.db.db_session import SessionLocal
from app.microservices.users.marg_sync_service import sync_products_from_marg_excel


# @router_v1.post("/data-dump")
# async def data_dump(
#     file: UploadFile = File(...),
#     sync_password: str = Form(...)
# ):
#     if not file.filename:
#         raise HTTPException(status_code=400, detail="File missing")

#     if not file.filename.lower().endswith((".xls", ".xlsx")):
#         raise HTTPException(status_code=400, detail="Invalid Excel file")

#     temp_dir = tempfile.mkdtemp()
#     file_path = os.path.join(temp_dir, file.filename)

#     db = SessionLocal()

#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         result = sync_products_from_marg_excel(
#             db=db,
#             file_path=file_path,
#             sync_password=sync_password,
#             system_user_id=None
#         )

#         return {
#             "status": "success",
#             "message": "Marg data synced successfully",
#             "result": result
#         }

#     except PermissionError as e:
#         raise HTTPException(status_code=401, detail=str(e))

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         db.close()
#         file.file.close()
#         shutil.rmtree(temp_dir, ignore_errors=True)




from fastapi import BackgroundTasks

@router_v1.post("/data-dump")
async def data_dump(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sync_password: str = Form(...)
):
    if not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Invalid Excel file")

    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file.file.close()  # ✅ IMPORTANT

    background_tasks.add_task( 
        run_marg_sync_job,
        file_path,
        sync_password
    )

    return {
        "status": "accepted",
        "message": "File received, sync started in background"
    }




# async def main():
#     async with get_async_session_context() as session:
#         await data_dump(
#             file="stock_51.xls",
#             session=session,
#             sync_password = "MARG_SYNC_123"
#         )
        

app.include_router(router_v1)

# if __name__ == "__main__":
    # asyncio.run(main())
    # uvicorn.run("app.microservices.users.users_routes:app", host="localhost", port=9000, reload=True)