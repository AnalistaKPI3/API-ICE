
#Para acceder a una base de datos dentro de un contenedor de PostgreSQL
docker exec -it postgres_b psql -U admeiasa -d tasks_ice


#restaurar desde un backup a un contenedor
docker exec -i postgres_b psql -U admeiasa -d tasks_ice < backup.sql