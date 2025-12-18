from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio

from app.db.db_session import async_session
from app.microservices.bigship.bigship_service import BigShipClient

client = BigShipClient()
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def refresh_bigship_token():
    async with async_session() as db:
        try:
            token = await client.force_refresh_token(db)
            print(f"[BigShip] Token refreshed at {datetime.now()} | token={token[:10]}...")
        except Exception as e:
            print(f"[BigShip] Token refresh failed: {e}")


def start_bigship_scheduler():
    # 5 AM
    scheduler.add_job(
        lambda: asyncio.create_task(refresh_bigship_token()),
        trigger="cron",
        hour=5,
        minute=0
    )

    # 5 PM
    scheduler.add_job(
        lambda: asyncio.create_task(refresh_bigship_token()),
        trigger="cron",
        hour=17,
        minute=0
    )

    scheduler.start()


