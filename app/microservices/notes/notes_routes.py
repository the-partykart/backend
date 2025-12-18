from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import Column, Integer, String, Date, DateTime, select, func
from sqlalchemy.orm import declarative_base
from datetime import date, datetime


from typing import List, Optional
from fastapi import FastAPI, Depends, BackgroundTasks, Query, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.db.services.category_repository import get_category_db
from app.db.services.offers_repository import get_offer_db
from app.db.services.order_alert_repository import new_order_db
from app.db.services.products_repository import check_product_name_db, get_product_db
from app.db.services.promocodes_repository import get_promocode_db
from app.microservices.buyed_product.buyed_product_schema import CartProductData, CartProductOfferData, ProductCategoryList, ProductCategoryList
from app.microservices.buyed_product.buyed_product_service import buy_product_service, generate_order_id, get_all_buy_product_service, get_buy_product_service, get_price_buy_product_service
from app.microservices.common_function import get_current_role, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import get_async_session
from app.db.models.db_base import Note, OrderItem, Users
from app.microservices.offers.offers_service import get_offer_service
from app.microservices.order_place.order_place_schema import OrderCreate
from app.microservices.order_place.order_place_service import create_order
from app.microservices.products.products_schema import CreateProduct, Updateproduct
from app.microservices.products.products_service import check_product_service, create_product_service, delete_product_service, get_all_product_service, get_product_service, update_product_service
# from app.microservices.sectors.sectors_service import check_sector_service
from app.microservices.promocodes.promocodes_service import get_promocode_service
from app.microservices.users.users_schema import Login, UpdateUserDetails, UserCreate
from app.utility.logging_utils import log_async, log_background 
from config.config import settings
from sqlalchemy.future import select
from app.db.models.db_base import Order
from sqlalchemy.orm import selectinload



prefix = settings.global_prefix

app = FastAPI()
router_v1 = APIRouter(prefix=f"/{prefix}/notes")

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ------------------------------------------------------------------
# SCHEMAS
# ------------------------------------------------------------------
class NoteCreate(BaseModel):
    note_text: str = Field(..., max_length=199)
    assigned_date: date

class NoteUpdate(BaseModel):
    note_text: str = Field(..., max_length=199)
    assigned_date: date


# ------------------------------------------------------------------
# CREATE NOTE
# ------------------------------------------------------------------
@router_v1.post("/create")
async def create_note(
    payload: NoteCreate,
    session: AsyncSession = Depends(get_async_session),
):
    note = Note(
        note_text=payload.note_text,
        assigned_date=payload.assigned_date,
    )

    session.add(note)
    await session.commit()
    await session.refresh(note)

    return {
        "message": "Note created",
        "note_id": note.note_id,
    }

# ------------------------------------------------------------------
# FETCH NOTES (PAGINATION)
# ------------------------------------------------------------------
@router_v1.get("/fetch")
async def fetch_notes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    session: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * limit

    total = await session.scalar(select(func.count(Note.note_id)))

    result = await session.execute(
        select(Note)
        .order_by(Note.assigned_date.desc())
        .offset(offset)
        .limit(limit)
    )

    notes = result.scalars().all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "note_id": n.note_id,
                "note_text": n.note_text,
                "assigned_date": n.assigned_date,
                "created_at": n.created_at,
            }
            for n in notes
        ],
    }

# ------------------------------------------------------------------
# GET NOTE BY ID
# ------------------------------------------------------------------
@router_v1.get("/get/{note_id}")
async def get_note(
    note_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Note).where(Note.note_id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "note_id": note.note_id,
        "note_text": note.note_text,
        "assigned_date": note.assigned_date,
        "created_at": note.created_at,
    }

# ------------------------------------------------------------------
# UPDATE NOTE
# ------------------------------------------------------------------
@router_v1.put("/update/{note_id}")
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Note).where(Note.note_id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.note_text = payload.note_text
    note.assigned_date = payload.assigned_date

    await session.commit()

    return {"message": "Note updated"}

# ------------------------------------------------------------------
# DELETE NOTE
# ------------------------------------------------------------------
@router_v1.delete("/delete/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Note).where(Note.note_id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await session.delete(note)
    await session.commit()

    return {"message": "Note deleted"}

# ------------------------------------------------------------------
# REGISTER ROUTER
# ------------------------------------------------------------------
app.include_router(router_v1)

# ------------------------------------------------------------------
# OPTIONAL: CREATE TABLES (DEV ONLY)
# ------------------------------------------------------------------
@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
