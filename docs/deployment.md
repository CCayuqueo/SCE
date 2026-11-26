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

GitHub Actions ensaya esa configuración en un proyecto Compose desechable
con HTTPS restringido a localhost, un certificado temporal y datos ficticios.
El runner comprueba migraciones, flujos de navegador y restauración, y audita
las imágenes de ejecución. La instalación en un servidor requiere validar por
separado el dominio, el certificado real y la ejecución programada del respaldo.

### Actualización desde PostgreSQL 17 en Debian

La base de Compose usa ahora la imagen Alpine de PostgreSQL 17 y el volumen
`pgdata_alpine`. Si una instalación anterior escribió datos en `pgdata`, conserva
ese volumen y toma un respaldo lógico desde la instalación anterior, antes de
cambiar de imagen. Detén las escrituras para el corte. Con la configuración
nueva, inicia solo el servicio `database`, restaura en una base vacía y verifica
la revisión de Alembic y los recuentos antes de iniciar la API. Las variantes
Debian y Alpine usan bibliotecas distintas para las reglas de ordenación. Evita
montar los archivos físicos del volumen Debian en la imagen Alpine.

## Aceptación en staging

Antes de publicar, comprueba en el servidor de staging:

1. El dominio redirige de HTTP a HTTPS. El certificado es válido para ese
   dominio y `/api/v1/health/ready` responde que PostgreSQL está disponible.
2. Alembic aplica las migraciones y `alembic check` pasa antes de validar la app.
3. Con usuarios de prueba y sus propias capturas, se puede crear y unir una sala,
   corregir el horario, confirmar y consultar la superposición. Verifica que un
   miembro regular no pueda acceder a esa vista. Completa la eliminación de
   cuenta con transferencia en una sala desechable.
4. El temporizador ejecuta un respaldo programado y la restauración en una base
   aparte conserva los datos esperados.

Registra la URL, el commit desplegado, las pruebas realizadas y los problemas
detectados en la bitácora. La suite automatizada crea y elimina datos de prueba:
ejecútala solo contra una base desechable.

### Base de datos y autenticación en Supabase

Usa un proyecto vacío de staging. En Supabase, desactiva la Data API del
proyecto. FastAPI se conecta a PostgreSQL y usa la API de Auth por separado.
En **Authentication → Sign In / Providers**, habilita Email y su confirmación,
conserva la confirmación segura del cambio de correo y fija un mínimo de 15
caracteres para las contraseñas. Configura SMTP para los correos de los usuarios
de aceptación. En **URL Configuration**, usa el origen HTTPS de SRC como **Site
URL** y agrega ese origen seguido de `/login` a **Redirect URLs**.

1. Desde `backend/`, ejecuta `alembic upgrade head` con `DATABASE_URL`
   configurada de forma privada para el administrador de ese proyecto. Usa la
   conexión directa o **Connect → Session pooler**. Usa TLS con verificación
   del certificado y un cliente PostgreSQL compatible. Mantén la cadena fuera
   del historial del shell, de Git y de los logs.
2. Ejecuta `infrastructure/supabase/permissions.sql` como `postgres` en el
   proyecto de staging. Crea el rol restringido `src_app`. Asigna una contraseña
   independiente de forma interactiva con `\password src_app` en `psql` y
   habilita su acceso con `ALTER ROLE src_app LOGIN`. El backend no necesita el
   rol administrador ni una API key elevada.
3. Configura `DATABASE_URL` para `src_app`, `SUPABASE_URL` con la URL HTTPS del
   proyecto y `SUPABASE_PUBLISHABLE_KEY` con su clave `sb_publishable_`. En el
   pooler compartido el usuario es `src_app.<project-ref>` y el puerto de sesión
   es `5432`. Copia el host del panel y configura `sslmode=verify-full` con el
   CA que corresponda a la conexión. Usa el origen HTTPS público de SRC para
   `APP_ORIGIN` y `APP_ENV=staging` durante la aceptación.
4. Comprueba `/api/v1/health/ready` y registra una cuenta nueva. Confirma el
   correo, inicia sesión, prueba los cambios de contraseña y correo y elimina
   una cuenta con transferencia de sala. Comprueba la revocación desde otro
   navegador. El entorno Compose local continúa usando PostgreSQL y Auth local
   cuando ambas variables de Supabase se omiten.

El respaldo programado del proyecto administrado debe incluir las identidades
de Auth y los datos de SRC. Ensaya su restauración en un proyecto separado.
El script de respaldo de Compose respalda su propia base local.

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

En un servidor con systemd, puedes usar las unidades de
`infrastructure/systemd/` para ejecutar el respaldo a las 03:00 de la hora
local. La plantilla supone que el repositorio está en `~/src` y que la cuenta
operadora tiene acceso a Docker. Si el repositorio está en otra ruta, cambia
`WorkingDirectory` y `ExecStart` en la copia de la unidad. Define
`SRC_BACKUP_DIR=/ruta/privada` en `~/.config/src/backup.env`, con permisos `0600`.

```bash
install -d -m 700 ~/.config/systemd/user
install -m 644 infrastructure/systemd/src-backup.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start src-backup.service
systemctl --user enable --now src-backup.timer
systemctl --user list-timers src-backup.timer
```

Revisa el primer resultado en `journalctl --user -u src-backup.service`.
Si el respaldo debe ejecutarse sin sesiones abiertas, la cuenta operadora
necesita un gestor de servicios de usuario activo al arrancar el servidor.

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
