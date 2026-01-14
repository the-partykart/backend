import sys
import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import quote_plus
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# ✅ Custom Proxy Middleware (simple version)
class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        proto = request.headers.get("x-forwarded-proto")
        if proto:
            request.scope["scheme"] = proto
        return await call_next(request)

# ✅ Imports for routers
from app.microservices.users.users_routes import router_v1 as users_router
from app.microservices.products.products_routes import router_v1 as products_router
from app.microservices.category.category_routes import router_v1 as category_router
# from app.microservices.offers.offers_routes import router_v1 as offers_router
# from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
# from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router
from app.microservices.order_place.order_place_routes import router_v1 as place_order
from app.microservices.courses.courses_routes import router as courses_route
from app.microservices.bigship.bigship_routes import router_v1 as bigship_route
from app.microservices.notes.notes_routes import router_v1 as notes_route
from app.microservices.bill_sample.bill_main import router as bill_route


# ✅ Import DB settings
from config.config import settings

# ✅ DB connection
DB_URL = f"mysql+asyncmy://{settings.db_username}:{quote_plus(settings.db_password)}@{settings.db_server}:{settings.db_port}/{settings.db_database_name}"
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="The Party Kart Backend",
    version="1.0",
    docs_url="/v1/docs",
    lifespan=lifespan,
    redirect_slashes=False

)

# ✅ Add Middleware
app.add_middleware(ProxyHeadersMiddleware)  # fixes HTTPS detection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routes
app.include_router(users_router)
app.include_router(products_router)
app.include_router(category_router)
# app.include_router(offers_router)
# app.include_router(promocodes_router)
# app.include_router(buyed_router)
app.include_router(order_alert_router)
app.include_router(place_order)
app.include_router(courses_route)
app.include_router(bigship_route)
app.include_router(notes_route)
app.include_router(bill_route)

@app.get("/")
def root():
    return {"message": "Backend running 🚀"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000)
