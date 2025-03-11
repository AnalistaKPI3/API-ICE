# Usar una imagen ligera de Python
FROM python:3.12-slim

# Establecer el directorio de trabajo como la raíz del proyecto
WORKDIR /API-ICE

# Copiar todos los archivos del proyecto al contenedor
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Exponer el puerto donde correrá FastAPI
EXPOSE 9090

# Comando para ejecutar FastAPI con Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9090"]