from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os

load_dotenv()



POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = os.getenv("DATABASE_URL")

# Servidor LINUX
#SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db_ice:5432/${POSTGRES_DB}"



# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={}, future=True)
# Configuración del engine con SSL requerido
engine = create_engine(
    #SQLALCHEMY_DATABASE_URL
    DATABASE_URL,
    # connect_args={
    #     "sslmode": "require",
    # },
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
