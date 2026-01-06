# from fastapi import Depends, HTTPException, BackgroundTasks, status
# from fastapi.responses import JSONResponse
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.db.db_session import get_async_session
# from app.db.services.promocodes_repository import create_promocode_db, delete_promocode_db, get_all_promocode_db, get_promocode_db, update_promocode_db
# from app.db.services.promocodes_repository import create_promocode_db
# from app.microservices.common_function import object_to_dict
# from app.utility.logging_utils import log_async 

# from datetime import datetime



# # Validation
# async def check_promocode_service(
#         promocode_id: int,
#         session: AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await get_promocode_db(
#             promocode_id= promocode_id,
#             session=session,
#             background_tasks=background_tasks,
#         )

#         if not result or result is None:
#             raise HTTPException(detail="promocode Not Found", status_code= status.HTTP_404_NOT_FOUND)
#         elif result.promocode_id and result.is_deleted==True:
#             raise HTTPException(detail="promocode Not Found (promocode Deleted)", status_code= status.HTTP_404_NOT_FOUND)
#         else:
#             return result

#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Error in Create promocode: {e}"
#         )


# async def create_promocode_service(
#         promocode_name,
#         promocode_percentage,
#         promocode_description,
#         user_id,
#         session: AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await create_promocode_db(
#             promocode_name = promocode_name,
#             promocode_percentage = promocode_percentage,
#             promocode_description =  promocode_description,
#             user_id = user_id,
#             session = session,
#             background_tasks = background_tasks,
#         )

#         if result:
#             return {
#                 "status":1,
#                 "message":"promocode create successfully"
#                 }
        
#         else:
#             return False
        
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode_SERVICE][CREATE_promocode_SERVICE] Error in create promocode Service: Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(
#             status_code=404,
#             detail=f"Error in Create promocode: {e}"
#         )

# async def get_all_promocode_service(
#         session:AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await get_all_promocode_db(
#             session=session,
#             background_tasks=background_tasks
#             )
        
#         if result:
#             data = [await object_to_dict(result_data) for result_data in result]
#             return data
        
#         if result is None:
#             return None
        
#         else:
#             log_async(
#                 background_tasks=background_tasks,
#                 message=f"[promocode][GET_ALL_promocode] Error: Failed Logic to Fetch all promocode. Exception: {e}",
#                 level="error",
#                 always_sync=True
#             )
#             raise HTTPException(status_code=500, detail="Failed Logic to Fetch all promocode.")


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
    


# async def get_promocode_service(
#         promocode_id:int,
#         session:AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await get_promocode_db(
#             promocode_id=promocode_id,
#             session=session,
#             background_tasks=background_tasks
#             )
        
#         if result:
#             # data = {
#             #     col.name: getattr(result, col.name).isoformat() if isinstance(getattr(result, col.name), datetime) else getattr(result, col.name)
#             #     for col in result.__table__.columns
#             # }
#             # return data
#             data = {
#             "promocode_id": result.promocode_id,
#             "promocode_name": result.promocode_name,
#             "promocode_percentage":result.promocode_percentage,
#             "created_by": result.created_by,
#             "created_at": result.created_at.isoformat() if result.created_at else None,
#             "updated_by": result.updated_by,
#             "updated_at": result.updated_at.isoformat() if result.updated_at else None,
#             "is_deleted": result.is_deleted,
#             "deleted_by": result.deleted_by,
#             "deleted_at": result.deleted_at.isoformat() if result.deleted_at else None,
#             }
#             return data
        
#         if result is None:
#             return None
        
#         else:
#             log_async(
#                 background_tasks=background_tasks,
#                 message=f"[promocode][GET_promocode] Error: Failed Logic to Fetch promocode. Exception: {e}",
#                 level="error",
#                 always_sync=True
#             )
#             raise HTTPException(status_code=500, detail="Failed Logic to Fetch promocode.")


#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode][GET_ALL_promocode] Error: Failed to Fetch promocode. Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(status_code=500, detail=f"Failed to Fetch promocode.{e}")


# async def update_promocode_service(
#         promocode_id,
#         promocode_name,
#         promocode_percentage,
#         promocode_description,
#         user_id,
#         current_promocode_name,
#         session: AsyncSession,
#         background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await update_promocode_db(
#             promocode_id = promocode_id,
#             promocode_name=promocode_name,
#             promocode_percentage=promocode_percentage,
#             promocode_description=promocode_description,
#             current_promocode_name=current_promocode_name,
#             user_id = user_id,
#             session = session,
#             background_tasks = background_tasks,
#         )

#         if result:
#             return{"status":1,"message":"promocode Update successfully"}
        
#         else:
#             return False
        
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode_SERVICE][CREATE_promocode_SERVICE] Error in create promocode Service: Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(
#             status_code=404,
#             detail=f"Error in Create promocode: {e}"
#         )
    
# async def delete_promocode_service(
#     promocode_id,
#     user_id,
#     current_promocode_name,
#     session: AsyncSession,
#     background_tasks: BackgroundTasks,
# ):
#     try:
#         result = await delete_promocode_db(
#             promocode_id = promocode_id,
#             current_promocode_name=current_promocode_name,
#             user_id = user_id,
#             session = session,
#             background_tasks = background_tasks,
#         )

#         if result:
#             return True
        
#         else:
#             return False
    
#     except HTTPException as http_exc:
#         raise http_exc

#     except Exception as e:
#         log_async(
#             background_tasks=background_tasks,
#             message=f"[promocode_SERVICE][DELETE_promocode_SERVICE] Error in Delete promocode Service: Exception: {e}",
#             level="error",
#             always_sync=True
#         )
#         raise HTTPException(
#             status_code=404,
#             detail=f"Error in Delete promocode: {e}"
#         )