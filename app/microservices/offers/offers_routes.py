# '''
# All offer related CRUD operations
# '''

from fastapi import FastAPI, Depends, BackgroundTasks, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.offers_repository import check_offer_name_db
from app.microservices.common_function import get_current_role, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.models.db_base import Users
from app.microservices.offers.offers_schema import Createoffer, Updateoffer
from app.microservices.offers.offers_service import check_offer_service, create_offer_service, delete_offer_service, get_all_offer_service, get_offer_service, update_offer_service
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background 
from config.config import settings

prefix = settings.global_prefix

app = FastAPI()
router_v1 = APIRouter(prefix=f"/{prefix}/offers")

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router_v1.post("/create")
async def create_offer_handler(
    data : Createoffer,
    background_tasks : BackgroundTasks,
    session : AsyncSession = Depends(get_async_session),
    user : Users = Depends(get_current_user),
):
    try:
        user_id = user.user_id
        role_result = await get_current_role(
            user_id = user_id,
            background_tasks=background_tasks,
            session=session,
        )

        check_offer_name = await check_offer_name_db(
            offer_name = data.offer_name,
            session=session,
            background_tasks=background_tasks,
        )
        if check_offer_name:
            raise HTTPException(
                detail="offer Already Created",
                status_code=status.HTTP_409_CONFLICT
            )
        
        
        result = await create_offer_service(
            offer_name = data.offer_name,
            offer_percentage = data.offer_percentage,
            offer_description = data.offer_description,
            user_id=user.user_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result["status"]==1:
            return JSONResponse(content=result,status_code=status.HTTP_201_CREATED)
        
        else:
            raise HTTPException(detail={
                "status":0,
                "message":"Unable to create offer"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][CREATE_offer] Error: Failed to create offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail=" Failed to create offer")
        

@router_v1.get("/")
async def get_all_offer_handler(
    background_tasks: BackgroundTasks,
    # user: Users = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_all_offer_service(
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
            raise HTTPException(status_code=500, detail="Failed to Fetch all offer.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][GET_ALL_offer] Error: Failed to Fetch all offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch all offer.")
    

@router_v1.get("/{offer_id}")
async def get_offer_handler(
    offer_id : int,
    background_tasks: BackgroundTasks,
    session : AsyncSession = Depends(get_async_session),
):
    try:
        result = await get_offer_service(
            offer_id=offer_id,
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
                detail="Offer not found",
                status_code=status.HTTP_404_NOT_FOUND
                )
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Fetch offer.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][GET_ALL_offer] Error: Failed to Fetch offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Fetch offer.")
    
@router_v1.patch("/update/{offer_id}")
async def update_offer_handler(
    offer_id : int,
    data: Updateoffer,
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
        
        check_offer = await check_offer_service(
            offer_id=offer_id,
            session=session,
            background_tasks=background_tasks,
        )
        current_offer_name = check_offer.offer_name

        if data.offer_name:
            check_offer_name = await check_offer_name_db(
                offer_name = data.offer_name,
                session=session,
                background_tasks=background_tasks,
            )

            if check_offer_name:
                raise HTTPException(
                    detail="offer name Already Used",
                    status_code=status.HTTP_409_CONFLICT
                )
        
        result = await update_offer_service(
            offer_id=offer_id,
            offer_name=data.offer_name,
            offer_percentage=data.offer_percentage,
            offer_description =data.offer_description,
            user_id = user.user_id,
            current_offer_name=current_offer_name,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "data":result
            })
        
        else:
            raise HTTPException(status_code=500, detail="Failed to Update offer.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][UPDATE_offer] Error: Failed to Update offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update offer.")
    

@router_v1.put("/delete/{offer_id}")
async def delete_offer_handler(
    offer_id : int,
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

        check_offer = await check_offer_service(
            offer_id=offer_id,
            session=session,
            background_tasks=background_tasks,
        )

        current_offer_name = check_offer.offer_name

        result = await delete_offer_service(
            current_offer_name=current_offer_name,
            user_id= user.user_id,
            offer_id=offer_id,
            session=session,
            background_tasks=background_tasks,
        )

        if result:
            return JSONResponse(content={
                "status":1,
                "message":"offer Delete Successfully"
            })
        
        else:
            raise HTTPException(
                detail="Unable to Delete offer",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        log_async(
            background_tasks=background_tasks,
            message=f"[offer][UPDATE_offer] Error: Failed to Update offer. Exception: {e}",
            level="error",
            always_sync=True
        )
        raise HTTPException(status_code=500, detail="Failed to Update offer.")

app.include_router(router_v1)

# if __name__=="__main__":
#     uvicorn.run("app.microservices.offers.offers_routes:app", host="0.0.0.0", port=9012,reload=True)


