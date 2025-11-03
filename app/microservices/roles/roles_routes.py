# '''
# All user related CRUD operations
# '''

from types import SimpleNamespace
from fastapi import FastAPI, Depends, BackgroundTasks, status
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
import sys

import sys
from sqlalchemy.ext.asyncio import AsyncSession

from app.microservices.users.users_schema import Login 


app = FastAPI()
router_v1 = APIRouter(prefix="/v1")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


