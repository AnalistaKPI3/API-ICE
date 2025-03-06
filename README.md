import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.tasks import task

from loguru import logger
import sys
from fastapi.middleware.cors import CORSMiddleware
from config.db import engine, get_db

from models import task as task_model
import sytex.findtasks as findtasks
from sytex.task_sync import run_task_sync


task_model.Base.metadata.create_all(bind=engine)

sync_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar la tarea de sincronización al arrancar la aplicación
    global sync_task
    db = next(get_db())
    sync_task = asyncio.create_task(run_task_sync(db))
    yield
    # Cancelar la tarea al cerrar la aplicación
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan, title="API PRODUCTIVIDAD - ICE")
# app = FastAPI(title="API PRODUCTIVIDAD - ICE")


# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("app.log", rotation="500 MB", retention="7 days")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(task)

# findtasks.main()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)


# if __name__ == "__main__":
#     asyncio.run(run_task_sync(get_db()))
