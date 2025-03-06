from datetime import datetime, timedelta
from io import BytesIO
import json
from sqlalchemy import or_, and_
import os
import sys
from fastapi import APIRouter, Depends, File, UploadFile
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


# from requests import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import get_db
from sqlalchemy.orm import Session

from fastapi.responses import JSONResponse
from loguru import logger

from models.task import Task, TaskCreate
from datetime import datetime, time

task = APIRouter(
    prefix="/api/tasks", tags=["Tareas"], responses={404: {"msg": "No encontrado"}}
)


eventscost = {
    "L01- Inst. Voz Cobre": 46.5928,
    "L02- Inst. Cobre (D,V+D)": 61.3347,
    "L03- Agrega D, VoIP": 34.8898,
    "L04- Inst. Caja Fachada (voz)": 34.7712,
    "L05- Inst. Caja Interna (voz)": 26.8658,
    "L06- Inst. TV Cobre (ind, duo o triple) o agrega TV": 105.1937,
    "L07- Inst. TV FO (ind, duo o triple)": 113.0344,
    "L08- Inst. FO (V,D,V+D)": 70.4850,
    "L09- Migración (V,D,V+D)": 97.7942,
    "L10- Migración y agrega (D+TV,TV)": 52.3900,
    "L11- Agrega STB (IFSD y/o IFHD)": 113.8467,
    "L12- Agrega TV FO": 67.4114,
    "L13- Inst.multilinea": 31.5515,
    "L14- ICRI": 47.2399,
    "L15- ICRE": 48.8160,
}


@task.get("/")
def find_all(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()

    return tasks


@task.post("/")
async def create_task(form: TaskCreate, db: Session = Depends(get_db)):
    cost = eventscost.get(form.event, 0)
    task = Task(**form.dict(), cost=cost)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@task.post("/upload-returned/")
async def upload_returned(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        excel_data = BytesIO(contents)
        df = pd.read_excel(excel_data)

        required_columns = [
            "code",
            "returned_well",
        ]

        if not all(col in df.columns for col in required_columns):
            return {"error": "Columnas requeridas faltantes en el Excel"}

        successful_updates = 0
        failed_updates = 0
        error_task_notfound = []

        for index, row in df.iterrows():
            try:

                code = row["code"]
                if not pd.isna(code):
                    code = str(int(code))

                task = db.query(Task).filter(Task.code == code).first()

                if task:

                    # print("Task", row["returned_well"])

                    if row["returned_well"] == 1:
                        task.returned_well = 1
                    else:
                        task.returned_well = 0
                    # task.returned_well = (
                    #     row["returned_well"]
                    #     if not pd.isna(row["returned_well"])
                    #     else None
                    # )

                    try:
                        db.commit()
                        successful_updates += 1
                    except Exception as commit_error:
                        db.rollback()
                        raise commit_error
                else:
                    error_task_notfound.append(row["code"])
                    failed_updates += 1

            except Exception as e:
                failed_updates += 1
                db.rollback()
                logger.error(
                    f"Error actualizando fila {index + 1}, code: {row['code']}: {str(e)}"
                )
                continue

        if error_task_notfound:
            ERROR_FILE_PATH = "returned_errors.txt"
            error_details = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "errors": [code for code in error_task_notfound],
            }

            with open(ERROR_FILE_PATH, "w") as f:
                json.dump(error_details, f, indent=2, ensure_ascii=False)

        return JSONResponse(
            {
                "code": 200,
                "successful_tasks": successful_updates,
                "failed_updates": failed_updates,
                "total_rows_processed": len(df),
                "error_file": (
                    json.load(open(ERROR_FILE_PATH)) if error_task_notfound else None
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error general procesando archivo: {str(e)}")
        return {"error": str(e), "status": "error"}


@task.get("/byfilters/")
# async def get_tasks(
#     code: str = None, staff: str = None, db: AsyncSession = Depends(get_db)
# ):
#     query = select(Task)

#     if code:
#         query = query.where(Task.code == code)
#     if staff:
#         query = query.where(Task.staff == staff)

#     result = db.execute(query)
#     tasks = result.scalars().all()


#     return [
#         {
#             "code": task.code,
#             "task_group": task.task_group,
#             "event": task.event,
#             "priceunit": task.priceunit,
#             "discount": task.discount,
#             "total": task.total,
#             "documenter": task.documenter,
#             "customer": task.customer,
#             "staff": task.staff,
#             "status": task.status,
#             "datedelivery_time": (
#                 task.datedelivery_time.isoformat() if task.datedelivery_time else None
#             ),
#             "completed_time": (
#                 task.completed_time.isoformat() if task.completed_time else None
#             ),
#             "returnedwell_time": (
#                 task.returnedwell_time.isoformat() if task.returnedwell_time else None
#             ),
#             "ejecution_time": task.ejecution_time,
#             "site": task.site,
#             "returned_well": task.returned_well,
#         }
#         for task in tasks
#     ]
async def get_tasks(
    code: str = None,
    staff: str = None,
    status: str = None,
    date_start: str = None,
    date_end: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Task)

    # Filtros básicos
    if code:
        query = query.where(Task.code == code)
    if staff:
        query = query.where(Task.staff == staff)
    if status:
        query = query.where(Task.status == status)

    # Filtro por rango de fechas dinámico según el estado
    if date_start or date_end:
        date_start_dt = (
            datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
        )
        date_end_dt = (
            datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)
            if date_end
            else None
        )

        # Condiciones para tareas devueltas (returnedwell_time)
        returned_condition = True
        if date_start_dt:
            returned_condition = and_(
                returned_condition, Task.returnedwell_time >= date_start_dt
            )
        if date_end_dt:
            returned_condition = and_(
                returned_condition, Task.returnedwell_time <= date_end_dt
            )

        # Condiciones para tareas completadas (completed_time)
        completed_condition = True
        if date_start_dt:
            completed_condition = and_(
                completed_condition, Task.completed_time >= date_start_dt
            )
        if date_end_dt:
            completed_condition = and_(
                completed_condition, Task.completed_time <= date_end_dt
            )

        # Aplicar filtro según el estado
        query = query.where(
            or_(
                # Tareas devueltas
                and_(Task.status.in_(["Devuelta", "MAL DEVUELTA"]), returned_condition),
                # Tareas completadas
                and_(Task.status == "Completada", completed_condition),
                # Otros estados (sin filtro de fecha o ajustable)
                Task.status.notin_(["Completada", "Devuelta", "MAL DEVUELTA"]),
            )
        )

    result = db.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "code": task.code,
            "task_group": task.task_group,
            "event": task.event,
            "priceunit": task.priceunit,
            "discount": task.discount,
            "total": task.total,
            "documenter": task.documenter,
            "customer": task.customer,
            "staff": task.staff,
            "status": task.status,
            "datedelivery_time": (
                task.datedelivery_time.isoformat() if task.datedelivery_time else None
            ),
            "completed_time": (
                task.completed_time.isoformat() if task.completed_time else None
            ),
            "returnedwell_time": (
                task.returnedwell_time.isoformat() if task.returnedwell_time else None
            ),
            "ejecution_time": task.ejecution_time,
            "site": task.site,
            "returned_well": task.returned_well,
        }
        for task in tasks
    ]
