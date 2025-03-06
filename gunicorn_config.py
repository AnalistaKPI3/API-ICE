import os

# Configuración de Gunicorn
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
keepalive = 120
timeout = 120
graceful_timeout = 120
max_requests = 1000
max_requests_jitter = 200
worker_connections = 1000
accesslog = "-"
errorlog = "-"
loglevel = "info"