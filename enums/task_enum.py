from enum import Enum


class TaskStatusEnum(Enum):
    abierta = "Abierta"
    asignada = "Asignada"
    completada = "Completada"
    cancelada = "Cancelada"
    devuelta = "Devuelta"
    encamino = "en camino"
    enproceso = "En proceso"
