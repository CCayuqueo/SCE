# SRC

SRC es una aplicación web para compartir horarios académicos en salas y analizar la disponibilidad semanal del grupo. El MVP contempla cuentas y sesiones, roles por sala, revisión y confirmación de horarios, y una vista consolidada con pesos de ocupación. Su alcance termina en el análisis de disponibilidad.

SRC incluye registro, sesiones, ajustes de cuenta y gestión de salas con roles locales, horarios editables y análisis de disponibilidad. El parser determinista se puede ejecutar por separado. Consulta el [estado de desarrollo](docs/DEVELOPMENT_PROGRESS.md) para ver las tareas y verificaciones pendientes.

## Arquitectura y requisitos

Nginx sirve el frontend React, TypeScript y Vite, y pasa las peticiones `/api/` a FastAPI. La API usa SQLAlchemy y psycopg para acceder a PostgreSQL. Alembic administra las migraciones. Docker Compose ejecuta los tres servicios y conserva PostgreSQL en un volumen.

- Con Docker: Docker Engine, Docker Compose v2 o compatible y OpenSSL para generar la contraseña local.
- Sin Docker: Node.js 24, npm, Python 3.13 y una instancia PostgreSQL 17 accesible.

## Ejecutar con Docker

Desde la raíz del repositorio, en la primera instalación:

```bash
cp -n .env.example .env
```

Configura `POSTGRES_PASSWORD` en `.env` con una contraseña propia. Puedes generar una con `openssl rand -hex 24`. Usa caracteres hexadecimales para que Compose pueda incorporarla a `DATABASE_URL`. Luego ejecuta:

```bash
docker compose up --build
```

Abre [http://localhost:3000](http://localhost:3000). La página consulta la API y muestra si PostgreSQL está disponible. También puedes comprobar los servicios desde la terminal:

```bash
curl -fsS http://localhost:3000/api/v1/health/live
curl -fsS http://localhost:3000/api/v1/health/ready
docker compose exec backend alembic current
docker compose down
```

`live` indica si FastAPI está funcionando. `ready` ejecuta una consulta a PostgreSQL y devuelve HTTP 503 si la base no está disponible. El proxy solo escucha en localhost. Si el puerto está ocupado, ajusta `SRC_HTTP_PORT` y `APP_ORIGIN`. El volumen se conserva al detener el entorno. Cambiar la contraseña en `.env` después de inicializar PostgreSQL no cambia la contraseña de su rol existente.

## Ejecutar localmente

Crea una base de datos de desarrollo vacía con un usuario que pueda crear tablas. Exporta `DATABASE_URL` con la URL de esa instancia en formato `postgresql+psycopg://usuario:contraseña@host:puerto/base`. Codifica los caracteres reservados de la contraseña si corresponde.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
cd backend
alembic upgrade head
APP_ORIGIN=http://localhost:5173 uvicorn app.main:app --reload --port 8000
```

En otra terminal, desde la raíz:

```bash
cd frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

Vite muestra la URL local y redirige `/api` a `http://127.0.0.1:8000`. Para cambiar ese destino, usa `SRC_API_PROXY_TARGET` al arrancar Vite. `VITE_API_BASE_URL` permite cambiar el prefijo del cliente al compilar, cuyo valor predeterminado es `/api/v1`.

## Autenticación

Puedes crear una cuenta en `/register` e iniciar sesión en `/login`. Tras autenticarte puedes entrar en `/app/inicio`, recargar y cerrar la sesión. FastAPI guarda hashes de contraseñas y tokens. El navegador conserva la sesión en una cookie `HttpOnly` y usa un token CSRF para cerrar sesión.

En `/app/ajustes` puedes editar el perfil, cambiar la contraseña o revisar el impacto de eliminar tu cuenta. Cambiar el correo requiere la contraseña actual. Cambiar la contraseña cierra las demás sesiones. Para eliminar la cuenta, revisa las salas afectadas, elige un sucesor o confirma el cierre de cada sala compartida que poseas, e introduce la contraseña actual y la palabra `ELIMINAR`.

Para clientes de la API, `GET /api/v1/users/me/deletion-preview` devuelve la vista previa con un encabezado `ETag`. Envía ese valor como `If-Match` en `POST /api/v1/users/me/deletion`, junto con el token CSRF. Un HTTP `409` indica que se debe volver a revisar la vista previa antes de confirmar.

`APP_ORIGIN` debe coincidir con el origen del navegador, incluyendo esquema y puerto. Configura HTTPS y `APP_ENV=production` para producción. Los límites de sesión se configuran con `SESSION_TTL_HOURS` y `SESSION_IDLE_MINUTES`, con valores iniciales de 24 horas y 60 minutos. Los intentos de registro y login se limitan por cuenta e IP en el proceso de FastAPI. El despliegue inicial usa un solo proceso.

## Salas

En `/app/salas` puedes crear una sala o unirte con un código de 12 caracteres.
Propietarios y administradores pueden consultar y copiar el código desde el detalle,
editar la información y promover integrantes. Solo el propietario puede revocar un
rol de administrador, expulsar a un integrante, transferir la propiedad o eliminar
la sala. Después de transferirla, el propietario anterior pasa a ser administrador.
Los demás integrantes pueden abandonar la sala desde su detalle.

La capacidad predeterminada es de 100 integrantes por sala, incluido el propietario.
Puedes ajustarla con `MAX_ROOM_MEMBERS` en el entorno del backend o en `.env` si usas Compose.

## Horario personal

Abre una sala y entra en **Mi horario**. Selecciona una captura que muestre las
siete columnas y los diez bloques completos. Se recomienda PNG. La API también
acepta JPEG, pero el parser puede rechazar los que pierden las líneas finas al
comprimir o reescalar. Las seis conversiones JPEG 4:2:0 ensayadas perdieron la
grilla. Una conversión 4:4:4 de alta calidad conserva sus coordenadas en la
prueba de compatibilidad.

La carga exitosa crea un borrador. Puedes cambiar cada celda libre u ocupada,
descartar los cambios locales o guardar y confirmar. Reemplazar un horario
confirmado requiere confirmación previa. La captura se elimina al terminar el
procesamiento. Si una carga falla, se conserva el horario anterior.

El límite inicial es de 5 MiB y 12 millones de píxeles. La API anuncia el
límite de bytes al consultar el horario. Se configura con `MAX_UPLOAD_MB`
(hasta 10 MiB), `MAX_IMAGE_PIXELS`, `IMAGE_PROCESSING_TIMEOUT_SECONDS` e
`IMAGE_PROCESSING_CONCURRENCY`.

## Superposición y horarios individuales

Como propietario o administrador, abre una sala y entra en **Superposición**.
Cada bloque muestra cuántos integrantes confirmados están ocupados. El color
representa esa cantidad como proporción de todos los integrantes de la sala.
Selecciona un bloque para ver las personas ocupadas, disponibles y pendientes.
Un peso de cero solo indica disponibilidad total si todos confirmaron. La
cobertura indica qué proporción tiene un horario confirmado.

En **Horarios individuales** puedes elegir a un integrante y consultar su grilla
confirmada en modo de solo lectura. Si tiene un borrador, se muestra su estado
pendiente sin revelar sus celdas.

## Migraciones y pruebas

Compose aplica `alembic upgrade head` antes de iniciar FastAPI. La revisión base es `0001`. La revisión `0002` crea `users`, `rooms`, `room_members`, `schedules`, `schedule_blocks` y `sessions`, con restricciones de integridad y eliminación en cascada.

Desde `backend/` y con el entorno Python activado:

```bash
ruff check .
ruff format --check .
pytest
# Con DATABASE_URL apuntando a una base PostgreSQL de pruebas:
alembic upgrade head
pytest -m integration
alembic check
```

Desde `frontend/`, después de `npm ci`:

```bash
npm run lint
npm run format:check
npm test
npm run build
```

Desde la raíz, con las dependencias Python instaladas:

```bash
python horario_parser.py "images/Captura de pantalla_2026-11-25_15-04-01.png"
python horario_parser.py images
```

## Estructura y documentación

- `frontend/`: aplicación web y pruebas de cliente.
- `backend/`: API, configuración, migraciones y pruebas Python.
- `infrastructure/nginx/`: configuración del proxy.
- `horario_parser.py` e `images/`: procesador determinista y capturas de referencia existentes.
- [Plan maestro](SRC_Plan_Maestro_Desarrollo_V1.md), [bitácora](docs/DEVELOPMENT_LOG.md), [estado](docs/DEVELOPMENT_PROGRESS.md) y [decisiones técnicas](docs/TECHNICAL_DECISIONS.md).

**Equipo desarrollador:** composición pendiente de confirmación.
