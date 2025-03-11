from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:eia.2022@localhost/task_ice"

# Servidor LINUX
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:hjdCSLnhGcNNxginapydanzGIlroQvfJ@trolley.proxy.rlwy.net:47391/railway"



# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={}, future=True)
# Configuración del engine con SSL requerido
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
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
