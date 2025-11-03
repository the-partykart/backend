# '''
# All user related CRUD operations
# '''

from typing import Optional
from fastapi import FastAPI, Depends, BackgroundTasks, File, Form, UploadFile, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.category_repository import check_category_name_db, check_sub_category_name_db
from app.microservices.common_function import get_current_role, get_current_user
from app.microservices.category.category_schema import Createcategory, Updatecategory
from app.microservices.category.category_service import check_sub_category_service, create_category_service, check_category_service, create_sub_category_service, delete_category_service, delete_sub_category_service, get_all_category_service, get_all_sub_category_service, get_category_details_service, get_category_service, get_sub_category_service, update_category_service, update_sub_category_service

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session 
from app.db.models.db_base import Users
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background 
from config.config import settings

global_prefix = settings.global_prefix
app = FastAPI(redirect_slashes=False)
router_v1 = APIRouter(prefix=f"/{global_prefix}/category")

from fastapi.middleware.cors import CORSMiddleware


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     # allow_credentials=False,    
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@router_v1.post("/create")
async def create_category_handler(
    # data : Createcategory,
    background_tasks : BackgroundTasks,
    category_name: str = Form(...),
    file: Optional[UploadFile] = File(None),
    session : AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),
    # user = Users(user_id=1),

):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        file = file
        if file is None:
            category_image = None

        else:
            category_image = file


        check_category_name = await check_category_name_db(
            category_name = category_name,
            session=session,
            background_tasks=background_tasks,
        )

        if check_category_name:
            raise HTTPException(
                detail="Category Already Created",
                status_code=status.HTTP_409_CONFLICT
            )
        
        result = await create_category_service(
            category_name = category_name,
            category_image=category_image,
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"]==1:
            return JSONResponse(content=result,status_code=status.HTTP_201_CREATED)
        
        else:
            raise HTTPException(detail={
                "status":0,
                "message":"Unable to create category"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][CREATE_category] Error: Failed to create category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=" Failed to create category")
        

@router_v1.get("/")
async def get_all_category_handler(
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    # user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_all_category_service(
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,      
                "data":result
            })
        
        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":[]
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch all category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category_route1] Error: Failed to Fetch all category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all category.")
    

@router_v1.get("/{category_id}")
async def get_category_handler(
    category_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_category_service(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })

        if result is None:
            raise HTTPException(
                detail="Category not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category_route3] Error: Failed to Fetch category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch category.")
    
@router_v1.patch("/update/{category_id}")
async def update_category_handler(
    category_id : int,
    background_tasks: BackgroundTasks,
    category_name : Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        file = file
        if file is None:
            category_image = None

        else:
            category_image = file

        check_category = await check_category_service(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks,
        )
        current_category_name = check_category.category_name

        check_category_name = await check_category_name_db(
            category_name = category_name,
            session=session,
            background_tasks=background_tasks,
        )
        if check_category_name:
            raise HTTPException(
                detail="category Already Used",
                status_code=status.HTTP_409_CONFLICT
            )
        
        result = await update_category_service(
            category_id=category_id,
            category_name=category_name,
            category_image= category_image,
            user_id = user.user_id,
            current_category_name=current_category_name,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Update category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][UPDATE_category] Error: Failed to Update category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update category.")
    
@router_v1.put("/delete/{category_id}")
async def delete_category_handler(
    category_id : int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        check_category = await check_category_service(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks,
        )

        current_category_name = check_category.category_name

        # is_deleted = check_category.is_deleted
        # if is_deleted == True or is_deleted==1:
        #     raise HTTPException(
        #         detail="category Already deleted",
        #         status_code=status.HTTP_404_NOT_FOUND
        #     )

        result = await delete_category_service(
            current_category_name=current_category_name,
            user_id= user.user_id,
            category_id=category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "message":"category Delete Successfully"
            })
        
        else:
            raise HTTPException(
                detail="Unable to Delete category",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][UPDATE_category] Error: Failed to Update category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update category.")
    


@router_v1.get("/details/{category_id}")
async def get_category_sub_category_handler(
    category_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    # user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_category_details_service(
            category_id=category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            
            return JSONResponse(content={
                "status":1,
                "data":result
            })

        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":None
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[category][GET_ALL_category_route2] Error: Failed to Fetch category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch category.")
    

####  ========== sub category ===========

@router_v1.post("/sub-category/create")
async def create_category_handler(
    # data : Createcategory,
    background_tasks : BackgroundTasks,
    sub_category_name: str = Form(...),
    category_id:int = Form(...),
    file: Optional[UploadFile] = File(None),
    session : AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),
    # user = Users(user_id=1),

):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        file = file
        if file is None:
            sub_category_image = None

        else:
            sub_category_image = file


        check_sub_category_name = await check_sub_category_name_db(
            sub_category_name = sub_category_name,
            session=session,
            background_tasks=background_tasks,
        )

        if check_sub_category_name:
            raise HTTPException(
                detail="Sub Category Already Created",
                status_code=status.HTTP_409_CONFLICT
            )
        
        result = await create_sub_category_service(
            sub_category_name = sub_category_name,
            sub_category_image = sub_category_image,
            category_id=category_id,
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"]==1:
            return JSONResponse(content=result,status_code=status.HTTP_201_CREATED)
        
        else:
            raise HTTPException(detail={
                "status":0,
                "message":"Unable to create sub_category"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][sub_CREATE_category] Error: Failed to create sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=" Failed to create sub_category")
        

@router_v1.get("/sub-category/")
async def get_all_sub_category_handler(
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    # user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_all_sub_category_service(
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,      
                "data":result
            })
        
        if result is None:
            return JSONResponse(content={
                "status":1,
                "data":"Empty"
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch all sub_category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][GET_ALL_sub_category] Error: Failed to Fetch all sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all sub_category.")
    

@router_v1.get("/sub-category/{sub_category_id}")
async def get_sub_category_handler(
    sub_category_id : int,
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    user = Users(user_id=1),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_sub_category_service(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })

        if result is None:
            raise HTTPException(
                detail="sub_Category not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch sub_category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][GET_ALL_sub_category] Error: Failed to Fetch sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch sub_category.")
    
@router_v1.patch("/sub-category/update/{sub_category_id}")
async def update_sub_category_handler(
    sub_category_id : int,
    background_tasks: BackgroundTasks,
    sub_category_name : Optional[str] = Form(None),
    category_id : Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        file = file
        if file is None:
            sub_category_image = None

        else:
            sub_category_image = file

        check_sub_category = await check_sub_category_service(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
        )
        current_sub_category_name = check_sub_category.sub_category_name

        check_category_name = await check_sub_category_name_db(
            sub_category_name = sub_category_name,
            session=session,
            background_tasks=background_tasks,
        )
        if check_category_name:
            raise HTTPException(
                detail="sub_category Already Used",
                status_code=status.HTTP_409_CONFLICT
            )
        
        result = await update_sub_category_service(
            sub_category_id=sub_category_id,
            category_id=category_id,
            sub_category_name=sub_category_name,
            sub_category_image= sub_category_image,
            user_id = user.user_id,
            current_sub_category_name=current_sub_category_name,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Update sub_category.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][UPDATE_sub_category] Error: Failed to Update sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update sub_category.")
    
@router_v1.put("/sub-category/delete/{sub_category_id}")
async def delete_sub_category_handler(
    sub_category_id : int,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        check_sub_category = await check_sub_category_service(
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
        )

        current_sub_category_name = check_sub_category.sub_category_name

        # is_deleted = check_category.is_deleted
        # if is_deleted == True or is_deleted==1:
        #     raise HTTPException(
        #         detail="category Already deleted",
        #         status_code=status.HTTP_404_NOT_FOUND
        #     )

        result = await delete_sub_category_service(
            current_sub_category_name=current_sub_category_name,
            user_id= user.user_id,
            sub_category_id=sub_category_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "message":"sub_category Delete Successfully"
            })
        
        else:
            raise HTTPException(
                detail="Unable to Delete sub_category",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[sub_category][UPDATE_sub_category] Error: Failed to Update sub_category. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update sub_category.")
    


app.include_router(router_v1)

# if __name__=="__main__":
#     uvicorn.run("app.microservices.category.category_routes:app", host="0.0.0.0", port=9008,reload=True)


