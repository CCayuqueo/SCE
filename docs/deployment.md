# Despliegue y recuperación

## Producción

Usa Docker Engine y una versión de Compose compatible con `!override`. Prepara
el DNS del dominio y un certificado válido que pueda renovarse. En el servidor,
configura `.env` con `APP_ORIGIN=https://tu-dominio`, credenciales de PostgreSQL y
`SRC_TLS_DIR` apuntando a un directorio que contenga `tls.crt` y `tls.key`.
Mantén el directorio de TLS y `.env` fuera del repositorio. Limita la exposición
pública a los puertos HTTP y HTTPS del proxy.

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml config -q
docker compose -f docker-compose.yml -f docker-compose.production.yml up --build --wait
```

Comprueba la redirección de HTTP, la carga por HTTPS y las respuestas de
`/api/v1/health/live` y `/api/v1/health/ready`. FastAPI aplica las migraciones antes
de arrancar. Verifica el mismo artefacto, un respaldo y las pruebas de navegador
en staging antes de promover una versión. Tras renovar el certificado, recarga
Nginx con `docker compose -f docker-compose.yml -f docker-compose.production.yml exec frontend nginx -s reload`.

Para PostgreSQL administrado en otro proveedor, adapta el despliegue a su conexión
TLS y suministra `DATABASE_URL` al backend como secreto. Usa un rol de aplicación
dedicado y limita el acceso de red al servidor SRC. Analiza las migraciones y los
permisos de acceso en staging antes de conectar datos reales.

## Observabilidad

Las respuestas incluyen `X-Request-ID`. Los logs de Nginx y FastAPI registran el
identificador, método, estado y duración. FastAPI agrega la clase de un error
inesperado sin el texto de la excepción. Conserva registros en un destino
con rotación y acceso restringido. Desde el monitoreo, comprueba disponibilidad
del proxy y `/api/v1/health/ready`.

## Respaldos y rollback

Ejecuta el respaldo como tarea diaria del servidor, con permisos solo para la
cuenta operadora. Guarda los archivos cifrados fuera del host con una retención
definida. Ejemplo desde la raíz del repositorio:

```bash
bash infrastructure/scripts/backup-db.sh /srv/src/backups \
  -f docker-compose.yml -f docker-compose.production.yml
```

Prueba la restauración periódicamente en una base nueva y aislada con acceso
restringido. Usa las herramientas cliente de PostgreSQL, una URL de conexión sin
credenciales en el comando (por ejemplo, usando un servicio y un archivo
`.pgpass` protegido), y un destino desechable:

```bash
pg_restore --exit-on-error --no-owner --no-privileges \
  --dbname 'service=src_restore' /ruta/al/respaldo.dump
```

Verifica la revisión de Alembic y los recuentos de usuarios, salas, membresías,
horarios y celdas. Comprueba también que las integridades y los flujos de inicio y
consulta siguen operativos. No conectes el entorno de pruebas a un respaldo con
datos reales sin limitar su acceso y deshabilitar sesiones previamente emitidas.

Antes de actualizar, conserva la versión de código e imágenes y un respaldo
verificado. Si el esquema es compatible, vuelve a las imágenes anteriores. Si
cambió de forma incompatible, detén las escrituras, restaura el respaldo en otra
base y apunta la versión anterior a esa base. Conserva la base original para
diagnóstico y reconciliación. Cualquier escritura posterior al respaldo requiere
una estrategia explícita antes de volver atrás.
