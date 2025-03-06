from datetime import datetime, timedelta
import asyncio
from decimal import ROUND_DOWN, Decimal
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .findtasks import FindTask, FindTask_desde_hasta
from models.task import Task
import logging
from sqlalchemy import func
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class TaskSynchronizer:
    def __init__(self, db: Session):
        self.db = db

    def _calculate_completion_time(
        self, task_data: Dict[Any, Any], status: str
    ) -> datetime:
        if status == "Completada":
            finish_date = task_data["results"][0]["finish_date"]
            finish_time = task_data["results"][0]["finish_time"]
            completion_datetime = datetime.strptime(
                f"{finish_date} {finish_time}", "%Y-%m-%d %H:%M:%S"
            ) - timedelta(hours=2)
            return completion_datetime
        elif status in ["Devuelta", "MAL DEVUELTA"]:
            when_last_edit = task_data["results"][0]["_when_last_edit"]
            dt = datetime.strptime(when_last_edit, "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt - timedelta(hours=5)
        return None

    def _get_ejecution_time(
        self, datetime_delivery: datetime, completed_time: datetime, status: str
    ):
        if status == "Completada":
            duration = Decimal(
                str((completed_time - datetime_delivery).total_seconds() / 3600)
            ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            return duration
        return None

    # todo:: _process_task_sync
    async def process_task(self, task_data: Dict[Any, Any]) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._process_task_sync, task_data)

    def _process_task_sync(self, task_data: Dict[Any, Any]) -> None:
        try:
            task_code = task_data["results"][0]["code"]
            current_status = task_data["results"][0]["status_step_display"]["name"][
                "name"
            ]
            description = task_data["results"][0]["description"]

            # Obtener precio base
            base_price = eventscost.get(task_data["results"][0]["name"], 0)
            info = self._parse_description(description)

            # Obtener fecha de entrega
            request_date = task_data["results"][0]["request_date"]
            request_time = task_data["results"][0]["request_time"]
            datetime_delivery = datetime.strptime(
                f"{request_date} {request_time}", "%Y-%m-%d %H:%M:%S"
            )

            # Calcular el tiempo actual y la fecha específica
            current_time = self._calculate_completion_time(task_data, current_status)
            current_date = (
                current_time.date() if current_time else datetime.now().date()
            )

            # Buscar registro existente para este task_group y el mismo día
            existing_task_same_day = (
                self.db.query(Task)
                .filter(
                    Task.task_group == task_code,
                    func.date(Task.created_at) == current_date,
                )
                .first()
            )

            # Obtener el registro más reciente para verificar el último estado
            latest_task = (
                self.db.query(Task)
                .filter(Task.task_group == task_code)
                .order_by(Task.created_at.desc())
                .first()
            )

            if existing_task_same_day:
                # Si ya existe un registro para el mismo día, actualizar solo si el estado cambió
                if existing_task_same_day.status != current_status:
                    if current_status == "Devuelta":
                        existing_task_same_day.returned_well = (
                            existing_task_same_day.returned_well or 0
                        ) + 1
                        existing_task_same_day.returnedwell_time = current_time
                        new_total = 12.54

                        # Sumar al total si es el mismo día y hay un estado previo
                        if (
                            latest_task
                            and latest_task.created_at.date() == current_date
                        ):
                            new_total += existing_task_same_day.total

                        existing_task_same_day.total = new_total
                        existing_task_same_day.status = current_status

                    elif current_status == "MAL DEVUELTA":
                        existing_task_same_day.returned_well = 0
                        discount = base_price * 0.25  # 25% de descuento
                        total_cost = base_price - discount

                        existing_task_same_day.total = total_cost
                        existing_task_same_day.discount = discount
                        existing_task_same_day.status = current_status

                    elif current_status == "Completada":
                        existing_task_same_day.completed_time = current_time
                        ejecution_time = self._get_ejecution_time(
                            datetime_delivery, current_time, current_status
                        )
                        existing_task_same_day.ejecution_time = ejecution_time

                        discount = base_price * 0.25 if ejecution_time > 42 else 0
                        total_cost = base_price - discount

                        # Sumar al total si es el mismo día y hay un estado previo
                        if (
                            latest_task
                            and latest_task.created_at.date() == current_date
                        ):
                            total_cost += existing_task_same_day.total

                        existing_task_same_day.total = total_cost
                        existing_task_same_day.discount = discount
                        existing_task_same_day.status = current_status

            else:
                # No hay registro para este día, crear uno nuevo solo si el estado cambió respecto al último
                if not latest_task or (
                    latest_task and latest_task.status != current_status
                ):
                    completion_time = None
                    returnedwell_time = None
                    ejecution_time = None
                    total_cost = 0
                    discount = 0

                    if current_status == "Completada":
                        completion_time = current_time
                        ejecution_time = self._get_ejecution_time(
                            datetime_delivery, completion_time, current_status
                        )
                        discount = base_price * 0.25 if ejecution_time > 42 else 0
                        total_cost = base_price - discount

                    elif current_status == "Devuelta":
                        returnedwell_time = current_time
                        total_cost = 12.54

                    elif current_status == "MAL DEVUELTA":
                        discount = base_price * 0.25
                        total_cost = base_price - discount

                    new_task = Task(
                        code=task_code,
                        task_group=task_code,
                        event=task_data["results"][0]["name"],
                        priceunit=base_price,
                        discount=discount,
                        total=total_cost,
                        documenter=task_data["results"][0]["assigned_staff"]["name"],
                        customer=info.get("customer_name", ""),
                        staff=task_data["results"][0]["assigned_staff"]["name"],
                        status=current_status,
                        datedelivery_time=datetime_delivery,
                        completed_time=completion_time,
                        returnedwell_time=returnedwell_time,
                        returned_well=1 if current_status == "Devuelta" else None,
                        ejecution_time=ejecution_time,
                        site=(
                            task_data["results"][0]["sites"][0]["name"]
                            if task_data["results"][0]["sites"]
                            else None
                        ),
                    )
                    self.db.add(new_task)

            self.db.commit()

        except Exception as e:
            logger.error(
                f"Error procesando tarea {task_data.get('code', 'unknown')}: {str(e)}"
            )
            self.db.rollback()

    def _parse_description(self, description: str) -> Dict[str, str]:
        info = {}
        lines = description.split("\n")
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                if "Nombre Cliente" in key:
                    info["customer_name"] = value.strip()
                elif "Evento" in key:
                    info["event"] = value.strip()
        return info

    async def sync_tasks(self) -> None:
        try:
            # Obtener tareas desde la API externa
            tasks_data = FindTask_desde_hasta()

            # Add debug logging
            logger.debug(f"tasks_data type: {type(tasks_data)}")

            # If tasks_data is a string, try to parse it as JSON
            if isinstance(tasks_data, str):
                import json

                tasks_data = json.loads(tasks_data)

            if tasks_data["count"] == 0:
                logger.info("No hay tareas nuevas para sincronizar")
                return

            tasks_list = [str(task["id"]) for task in tasks_data["results"]]

            # Procesar cada tarea
            for task_id in tasks_list:
                task_data = FindTask(task_id)
                await self.process_task(task_data)

        except Exception as e:
            logger.error(f"Error en sincronización: {str(e)}")
            # Add more detailed error logging
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")


async def run_task_sync(db: Session):
    print("Corriendo task sync")
    synchronizer = TaskSynchronizer(db)
    while True:
        await synchronizer.sync_tasks()
        await asyncio.sleep(60)  # Esperar 30 segundos
