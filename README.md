# SRC

SRC es una aplicación web para compartir horarios académicos en salas y analizar la disponibilidad semanal del grupo. El MVP contempla cuentas y sesiones, roles por sala, revisión y confirmación de horarios, y una vista consolidada con pesos de ocupación. Su alcance termina en el análisis de disponibilidad.

La base de la Fase 0 incluye una pantalla de estado, dos endpoints de salud, PostgreSQL y la configuración de migraciones. El parser determinista se puede ejecutar por separado. Consulta el [estado de desarrollo](docs/DEVELOPMENT_PROGRESS.md) para ver las verificaciones pendientes.

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
uvicorn app.main:app --reload --port 8000
```

En otra terminal, desde la raíz:

```bash
cd frontend
npm ci
npm run dev
```

Vite muestra la URL local y redirige `/api` a `http://127.0.0.1:8000`. Para cambiar ese destino, usa `SRC_API_PROXY_TARGET` al arrancar Vite. `VITE_API_BASE_URL` permite cambiar el prefijo del cliente al compilar, cuyo valor predeterminado es `/api/v1`.

## Migraciones y pruebas

Compose aplica `alembic upgrade head` antes de iniciar FastAPI. La revisión `0001` comprueba el recorrido desde una base vacía y deja la creación del esquema de negocio para la Fase 1.

Desde `backend/` y con el entorno Python activado:

```bash
ruff check .
ruff format --check .
pytest
# Con DATABASE_URL apuntando a PostgreSQL de pruebas:
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
