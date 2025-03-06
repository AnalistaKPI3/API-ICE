from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio A al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Importar el módulo completo
import sytex.Sytex as Sytex


def FindTask(id):
    Taskurl = "https://app.sytex.io/api/task/?id=" + id
    return Sytex.RunApi(Taskurl)


def FindTask_desde_hasta():

    # fecha_desde = "2025-01-01"
    # fecha_hasta = "2025-02-25"
    fecha_desde = (datetime.today() - timedelta(days=2)).strftime(
        "%Y-%m-%d"
    )  # Fecha hace 3 días
    fecha_hasta = datetime.today().strftime("%Y-%m-%d")  # Fecha actual

    if fecha_desde == fecha_hasta:
        Taskurl = f"https://app.sytex.io/api/task/?plan_date_duration={fecha_desde}&project=144528&task_template=741&status_step_name=1249&status_step_name=4014&status_step_name=4876&limit=4000"
    else:
        Taskurl = f"https://app.sytex.io/api/task/?task_template=741&project=144528&plan_date_duration=_{fecha_desde}_{fecha_hasta}_&status_step_name=1249&status_step_name=4014&status_step_name=4876&limit=4000"
    return Sytex.RunApi(Taskurl)
