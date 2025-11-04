# import multiprocessing
# import uvicorn
# import sys
# import os



# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# # Import routers
# from app.microservices.users.users_routes import router_v1 as users_router
# from app.microservices.products.products_routes import router_v1 as products_router
# from app.microservices.category.category_routes import router_v1 as category_router
# from app.microservices.offers.offers_routes import router_v1 as offers_router
# from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
# from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
# from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router

# app = FastAPI()

# # Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Register all routers
# app.include_router(users_router)
# app.include_router(products_router)
# app.include_router(category_router)
# app.include_router(offers_router)
# app.include_router(promocodes_router)
# app.include_router(buyed_router)
# app.include_router(order_alert_router)

# # Run all services on a single port
# # uvicorn app.main:app --host 0.0.0.0 --port 9000





# # ✅ Ensures Python can locate microservice modules
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # ✅ This function starts an individual FastAPI service via Uvicorn
# def start_services(app_module: str, port: int, service_name: str, reload: bool = False):
#     print(f"Attempting to start {service_name} on port {port}...")
#     try:
#         uvicorn.run(
#             app_module,
#             host="localhost",
#             port=port,
#             reload=reload, # ✅ Change 1: Make reload dynamic via CLI flag
#             timeout_keep_alive=10,         # ✅ Change 2: fixed syntax for keep-alive timeout
#             log_level="info"
#         )
#     except Exception as e:
#         print(f"ERROR: Unable to start {service_name} on port {port}: {e}", file=sys.stderr)


# if __name__ == "__main__":
#     # ✅ Change 2: Explicitly set start method to 'spawn'
#     # Reason: Required on Windows to avoid RuntimeError when using multiprocessing

#     if sys.platform == "win32":
#         multiprocessing.set_start_method("spawn", force=True)


#     # ✅ Ensures Windows can safely spawn subprocesses
#     multiprocessing.freeze_support()

#     # ✅ Change 3: Allow optional --reload flag via command line
#     # Usage: `python main.py --reload`
#     RELOAD_MODE = "--reload" in sys.argv

#     services = [
#         {
#             "app_module": "app.microservices.users.users_routes:app",
#             "port": 9000,
#             "service_name": "Users Service"
#         },
#         {
#             "app_module": "app.microservices.promocodes.promocodes_routes:app",
#             "port": 9016,
#             "service_name": "promocodes Service"
#         },
#         {
#             "app_module": "app.microservices.products.products_routes:app",
#             "port": 9004,
#             "service_name": "products Service"
#         },
#         {
#             "app_module": "app.microservices.offers.offers_routes:app",
#             "port": 9012,
#             "service_name": "offers Service"
#         },
#         {
#             "app_module": "app.microservices.category.category_routes:app",
#             "port": 9008,
#             "service_name": "Category Service"
#         },   
#         {
#             "app_module": "app.microservices.buyed_product.buyed_routes:app",
#             "port": 9020,
#             "service_name": "buyed product Service"
#         },
#         {
#             "app_module": "app.microservices.order_alert.order_alert_routes:app",
#             "port": 9024,
#             "service_name": "order alert Service"
#         },
#     ]

#     processes = []
#     print("Starting all microservices...")
#     for service_info in services:
#         p = multiprocessing.Process(
#             target=start_services,
#             args=(
#                 service_info["app_module"],
#                 service_info["port"],
#                 service_info["service_name"],
#                 RELOAD_MODE  # ✅ Pass reload mode to subprocesses
#             ),
#             name=service_info["service_name"]
#         )
#         processes.append(p)
#         p.start()

#     print("\nAll services initiated. Check console for logs from each service.")
#     print("Press Ctrl+C to gracefully stop all services.")

#     try:
#         for p in processes:
#             p.join()
#     except KeyboardInterrupt:
#         print("\nCtrl+C detected. Stopping all services...")
#         for p in processes:
#             if p.is_alive():
#                 print(f"Terminating {p.name} (PID: {p.pid})...")
#                 p.terminate()
#                 p.join(timeout=5)
#                 if p.is_alive():
#                     print(f"WARNING: {p.name} (PID: {p.pid}) did not terminate gracefully. Killing now.")
#                     p.kill()
#         print("All services stopped.")





### working below 

# import sys
# import os
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

# # ✅ Ensure Python can locate your microservice modules
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # ✅ Import routers from microservices
# from app.microservices.users.users_routes import router_v1 as users_router
# from app.microservices.products.products_routes import router_v1 as products_router
# from app.microservices.category.category_routes import router_v1 as category_router
# from app.microservices.offers.offers_routes import router_v1 as offers_router
# from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
# from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
# from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router

# # ✅ Create single FastAPI app
# # app = FastAPI(title="Inventory Shop Backend", version="1.0")

# app = FastAPI(
#     title="Inventory Shop Backend",
#     version="1.0",
#     docs_url="/v1/docs",
#     redoc_url="/v1/redoc"
# )


# # ✅ Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],   # In production, restrict to frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Register routers (from each service)
# app.include_router(users_router)
# app.include_router(products_router)
# app.include_router(category_router)
# app.include_router(offers_router)
# app.include_router(promocodes_router)
# app.include_router(buyed_router)
# app.include_router(order_alert_router)

# # ✅ Default root endpoint
# @app.get("/")
# def root():
#     return {"message": "Backend is running 🚀"}

# # ✅ Entry point to run the app directly
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=9000,
#         reload=False  # 👈 useful for development (auto-reload on code changes)
#     )



###################

# import sys
# import os
# import asyncio
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy import text
# import uvicorn
# from contextlib import asynccontextmanager
# from sqlalchemy.ext.asyncio import create_async_engine
# from urllib.parse import quote_plus

# # ✅ Ensure Python can locate your microservice modules
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # ✅ Import routers from microservices
# from app.microservices.users.users_routes import router_v1 as users_router
# from app.microservices.products.products_routes import router_v1 as products_router
# from app.microservices.category.category_routes import router_v1 as category_router
# from app.microservices.offers.offers_routes import router_v1 as offers_router
# from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
# from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
# from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router

# # ✅ Import DB settings (adjust if needed)

# from config.config import settings

# # ✅ Create Async SQLAlchemy engine for pings
# db_username = settings.db_username
# db_password = settings.db_password
# db_server = settings.db_server
# db_port = settings.db_port
# db_database_name = settings.db_database_name

# DB_URL = f"mysql+asyncmy://{db_username}:{quote_plus(db_password)}@{db_server}:{db_port}/{db_database_name}"
# engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

# # ✅ Lifespan context to keep DB alive

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     async def keep_db_alive():
#         while True:
#             try:
#                 async with engine.connect() as conn:
#                     await conn.execute(text("SELECT 1"))
#                     print("✅ [Keep-Alive] DB ping successful.")
#             except Exception as e:
#                 print(f"❌ [Keep-Alive] DB ping failed: {e}")
#             await asyncio.sleep(300)  # every 5 minutes

#     asyncio.create_task(keep_db_alive())
#     yield
    
# # ✅ Create FastAPI app with lifespan
# app = FastAPI(
#     title="Inventory Shop Backend",
#     version="1.0",
#     docs_url="/v1/docs",
#     redoc_url="/v1/redoc",
#     lifespan=lifespan
# )

# app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


# # ✅ Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Register routers
# app.include_router(users_router)
# app.include_router(products_router)
# app.include_router(category_router)
# app.include_router(offers_router)
# app.include_router(promocodes_router)
# app.include_router(buyed_router)
# app.include_router(order_alert_router)

# # ✅ Default root endpoint
# @app.get("/")
# def root():
#     return {"message": "Backend is running 🚀"}

# # ✅ Entry point to run the app directly
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=9000,
#         reload=False
#     )



# ----------------------------------------------------------

# import sys
# import os
# import asyncio
# from sqlalchemy import text
# import uvicorn
# from contextlib import asynccontextmanager
# from sqlalchemy.ext.asyncio import create_async_engine
# from urllib.parse import quote_plus
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# # ✅ Ensure Python can locate your microservice modules
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # ✅ Import routers
# from app.microservices.users.users_routes import router_v1 as users_router
# from app.microservices.products.products_routes import router_v1 as products_router
# from app.microservices.category.category_routes import router_v1 as category_router
# from app.microservices.offers.offers_routes import router_v1 as offers_router
# from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
# from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
# from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router

# # ✅ Import DB settings
# from config.config import settings

# # ✅ Create Async SQLAlchemy engine for pings
# db_username = settings.db_username
# db_password = settings.db_password
# db_server = settings.db_server
# db_port = settings.db_port
# db_database_name = settings.db_database_name

# DB_URL = f"mysql+asyncmy://{db_username}:{quote_plus(db_password)}@{db_server}:{db_port}/{db_database_name}"
# engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

# # ✅ Lifespan context to keep DB alive
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     async def keep_db_alive():
#         while True:
#             try:
#                 async with engine.connect() as conn:
#                     await conn.execute(text("SELECT 1"))
#                     print("✅ [Keep-Alive] DB ping successful.")
#             except Exception as e:
#                 print(f"❌ [Keep-Alive] DB ping failed: {e}")
#             await asyncio.sleep(300)  # every 5 minutes

#     asyncio.create_task(keep_db_alive())
#     yield


# # ✅ Create FastAPI app
# app = FastAPI(
#     title="Inventory Shop Backend",
#     version="1.0",
#     docs_url="/v1/docs",
#     redoc_url="/v1/redoc",
#     lifespan=lifespan,
# )

# # ✅ Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Change this to your frontend domain in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Register routers
# app.include_router(users_router)
# app.include_router(products_router)
# app.include_router(category_router)
# app.include_router(offers_router)
# app.include_router(promocodes_router)
# app.include_router(buyed_router)
# app.include_router(order_alert_router)

# # ✅ Root endpoint
# @app.get("/")
# def root():
#     return {"message": "Backend is running 🚀"}


# # ✅ Run the app with proper proxy header support (fix 307 HTTPS redirect)
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=9000,
#         reload=False,
#         proxy_headers=True,               # <── this is the key flag
#         forwarded_allow_ips="*",          # <── trust all proxies (CloudCluster, Nginx)
#     )




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
from app.microservices.offers.offers_routes import router_v1 as offers_router
from app.microservices.promocodes.promocodes_routes import router_v1 as promocodes_router
from app.microservices.buyed_product.buyed_routes import router_v1 as buyed_router
from app.microservices.order_alert.order_alert_routes import router_v1 as order_alert_router

# ✅ Import DB settings
from config.config import settings

# ✅ DB connection
DB_URL = f"mysql+asyncmy://{settings.db_username}:{quote_plus(settings.db_password)}@{settings.db_server}:{settings.db_port}/{settings.db_database_name}"
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def keep_db_alive():
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                    print("✅ [Keep-Alive] DB ping successful.")
            except Exception as e:
                print(f"❌ [Keep-Alive] DB ping failed: {e}")
            await asyncio.sleep(300)
    asyncio.create_task(keep_db_alive())
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
app.include_router(offers_router)
app.include_router(promocodes_router)
app.include_router(buyed_router)
app.include_router(order_alert_router)

@app.get("/")
def root():
    return {"message": "Backend running 🚀"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000)
