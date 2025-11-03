# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from contextlib import asynccontextmanager
# from urllib.parse import quote_plus

# # db_username = "root"
# # db_password = "root"
# # db_server = "127.0.0.1"
# # db_port = 3306
# # db_database_name = "pk"


# # db_name = "mysql"  # MySQL connection type (same as default in the original command)
# # db_drivername = "asyncmy"  # async driver for async operations
# # db_username = "root"  # username
# # db_password = "tBwvfLRHyGLObmtHWBngVvXxnKzOBCiG"  # password from the original command
# # db_port = 32991  # port provided in the original command
# # db_database_name = "railway"  # database name from the original command
# # db_server = "gondola.proxy.rlwy.net"  # server address from the original command
# # db_protocol = "TCP"  # protocol from the original command

# from config.config import settings

# db_name = settings.db_name
# db_drivername = settings.db_drivername
# db_username = settings.db_username
# db_password = settings.db_password
# db_port = settings.db_port
# db_database_name = settings.db_database_name
# db_server = settings.db_server

# DB_url = f"mysql+asyncmy://{db_username}:{quote_plus(db_password)}@{db_server}:{db_port}/{db_database_name}"

# # # Create async engine
# # async_engine = create_async_engine(DB_url, echo=False)

# # ✅ Create async engine with connection pooling
# async_engine = create_async_engine(
#     DB_url,
#     echo=False,                 # Turn on for debugging SQL
#     pool_size=10,               # Number of connections to keep open
#     max_overflow=20,            # Extra connections allowed during high load
#     pool_timeout=30,            # Seconds to wait before giving up
#     pool_recycle=1800,          # Recycle connections every 30 mins (avoid MySQL timeouts)
#     pool_pre_ping=True,         # Check connection health before using it
#     future=True
# )

# # Create async sessionmaker
# async_session_maker = sessionmaker(
#     async_engine, class_=AsyncSession, expire_on_commit=False
# )

# async def get_async_session() -> AsyncSession:
#     async with async_session_maker() as session:
#         yield session

# @asynccontextmanager
# async def get_async_session_context():
#     async with async_session_maker() as session:
#         yield session














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

# ✅ Build the async MySQL connection URL
DB_URL = f"mysql+{db_drivername}://{db_username}:{quote_plus(db_password)}@{db_server}:{db_port}/{db_database_name}"

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

# ✅ Create async session factory
async_session_maker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,     # Prevent data from expiring after commit
)

# ✅ Dependency for FastAPI routes
async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# ✅ Context manager for services or background tasks
@asynccontextmanager
async def get_async_session_context():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
