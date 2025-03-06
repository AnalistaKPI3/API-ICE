import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.tasks import task
from loguru import logger
import sys
from fastapi.middleware.cors import CORSMiddleware
from config.db import engine, get_db
from models import task as task_model
from sytex.task_sync import run_task_sync

task_model.Base.metadata.create_all(bind=engine)

sync_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sync_task
    db = next(get_db())
    sync_task = asyncio.create_task(run_task_sync(db))
    yield
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan, title="API PRODUCTIVIDAD - ICE")


logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("app.log", rotation="500 MB", retention="7 days")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task)
