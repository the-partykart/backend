# # '''
# # All promocode related CRUD operations
# # '''

# from fastapi import FastAPI, Depends, BackgroundTasks, status
# from fastapi import HTTPException, APIRouter
# from fastapi.responses import JSONResponse
# from datetime import datetime, timedelta, timezone

# from sqlalchemy.ext.asyncio import AsyncSession
# import uvicorn

# from app.db.services.promocodes_repository import check_promocode_name_db, check_promocode_name_db
# from app.microservices.common_function import get_current_role, get_current_user
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.db.db_session import get_async_session
# from app.db.models.db_base import Users
# from app.microservices.promocodes.promocodes_schema import CreatePromocode, CreatePromocode, UpdatePromocode
# from app.microservices.promocodes.promocodes_service import check_promocode_service, create_promocode_service, delete_promocode_service, get_all_promocode_service, get_promocode_service, update_promocode_service
# from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
# from app.utility.logging_utils import log_async, log_background 
# from config.config import settings

# prefix = settings.global_prefix

# app = FastAPI()
# router_v1 = APIRouter(prefix=f"/{prefix}/promocode")

# from fastapi.middleware.cors import CORSMiddleware


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     # allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @router_v1.post("/create")
# async def create_promocode_handler(
#     data : CreatePromocode,
#     background_tasks : BackgroundTasks,
#     session : AsyncSession = Depends(get_async_session),
#     user : Users = Depends(get_current_user),
# ):
#     try:
#         user_id = user.user_id
#         role_result = await get_current_role(
#             user_id = user_id,
#             background_tasks=background_tasks,
#             session=session,
#         )

#         check_promocode_name = await check_promocode_name_db(
#             promocode_name = data.promocode_name,
#             session=session,
#             background_tasks=background_tasks,
#         )
#         if check_promocode_name:
#             raise HTTPException(
#                 detail="promocode Already Created",
#                 status_code=status.HTTP_409_CONFLICT
#             )

#         result = await create_promocode_service(
#             promocode_name = data.promocode_name,
#             promocode_percentage = data.promocode_percentage,
#             promocode_description = data.promocode_description,
#             user_id=user.user_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result["status"]==1:
#             return JSONResponse(content=result,status_code=status.HTTP_201_CREATED)
        
#         else:
#             raise HTTPException(detail={
#                 "status":0,
#                 "message":"Unable to create promocode"
#             },
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][CREATE_promocode] Error: Failed to create promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail=" Failed to create promocode")
        

# @router_v1.get("/")
# async def get_all_promocode_handler(
#     background_tasks: BackgroundTasks,
#     # user: Users = Depends(get_current_user),
#     user= Users(user_id=1),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
#         result = await get_all_promocode_service(
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return JSONResponse(content={
#                 "status":1,      
#                 "data":result
#             })
        
#         if result is None:
#             return JSONResponse(content={
#                 "status":1,
#                 "data":"Empty"
#             })
        
#         else:
#             raise HTTPException(status_code=500, detail="Failed to Fetch all promocode.")

#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][GET_ALL_promocode] Error: Failed to Fetch all promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail="Failed to Fetch all promocode.")
    

# @router_v1.get("/{promocode_id}")
# async def get_promocode_handler(
#     promocode_id : int,
#     background_tasks: BackgroundTasks,
#     # user: Users = Depends(get_current_user),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
#         result = await get_promocode_service(
#             promocode_id=promocode_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return JSONResponse(content={
#                 "status":1,
#                 "data":result
#             })

#         if result is None:
#             raise HTTPException(
#                 detail="Promocode not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#                 )
        
#         else:
#             raise HTTPException(status_code=500, detail="Failed to Fetch promocode.")

#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][GET_ALL_promocode] Error: Failed to Fetch promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail="Failed to Fetch promocode.")
    
# @router_v1.patch("/update/{promocode_id}")
# async def update_promocode_handler(
#     promocode_id : int,
#     data: UpdatePromocode,
#     background_tasks: BackgroundTasks,
#     user: Users = Depends(get_current_user),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
#         user_id = user.user_id
#         role_result = await get_current_role(
#             user_id = user_id,
#             background_tasks=background_tasks,
#             session=session,
#         )

#         check_promocode = await check_promocode_service(
#             promocode_id=promocode_id,
#             session=session,
#             background_tasks=background_tasks,
#         )
#         current_promocode_name = check_promocode.promocode_name

#         if data.promocode_name:
#             check_promocode_name = await check_promocode_name_db(
#                 promocode_name = data.promocode_name,
#                 session=session,
#                 background_tasks=background_tasks,
#             )

#             if check_promocode_name:
#                 raise HTTPException(
#                     detail="promocode name Already Used",
#                     status_code=status.HTTP_409_CONFLICT
#                 )
        
#         result = await update_promocode_service(
#             promocode_id=promocode_id,
#             promocode_name=data.promocode_name,
#             promocode_percentage=data.promocode_percentage,
#             promocode_description =data.promocode_description,
#             user_id = user.user_id,
#             current_promocode_name=current_promocode_name,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return JSONResponse(content={
#                 "status":1,
#                 "data":result
#             })
        
#         else:
#             raise HTTPException(status_code=500, detail="Failed to Update promocode.")

#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][UPDATE_promocode] Error: Failed to Update promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail="Failed to Update promocode.")
    

# @router_v1.put("/delete/{promocode_id}")
# async def delete_promocode_handler(
#     promocode_id : int,
#     background_tasks: BackgroundTasks,
#     user: Users = Depends(get_current_user),
#     session : AsyncSession = Depends(get_async_session),
# ):
#     try:
#         user_id = user.user_id
#         role_result = await get_current_role(
#             user_id = user_id,
#             background_tasks=background_tasks,
#             session=session,
#         )

#         check_promocode = await check_promocode_service(
#             promocode_id=promocode_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         current_promocode_name = check_promocode.promocode_name

#         result = await delete_promocode_service(
#             current_promocode_name=current_promocode_name,
#             user_id= user.user_id,
#             promocode_id=promocode_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if result:
#             return JSONResponse(content={
#                 "status":1,
#                 "message":"promocode Delete Successfully"
#             })
        
#         else:
#             raise HTTPException(
#                 detail="Unable to Delete promocode",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

    
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][UPDATE_promocode] Error: Failed to Update promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail="Failed to Update promocode.")

# app.include_router(router_v1)

# # if __name__=="__main__":
# #     uvicorn.run("app.microservices.promocodes.promocodes_routes:app", host="0.0.0.0", port=9016,reload=True)


