# Bitácora de desarrollo — SRC V1

## 2026-11-25 — Fase 0 — Inventario, API y entorno de datos

### Objetivo
Identificar el punto de partida y preparar FastAPI, SQLAlchemy y Alembic.

### Cambios implementados
- Se conservó el repositorio existente y el parser. Existían `main`, `develop` y seis capturas versionadas; no había remoto configurado.
- Se añadieron la configuración de secretos locales, la API con dos verificaciones de salud y la revisión base de Alembic.

### Archivos creados
- `.gitignore`, `.env.example`, `backend/app/`, `backend/alembic.ini`, `backend/migrations/`, `backend/pyproject.toml` y archivos de dependencias Python.

### Archivos modificados
- Ningún archivo preexistente.

### Decisiones técnicas
- ADR-002 documenta la separación de la revisión base y el esquema de negocio.

### Comandos ejecutados
- `git status --short --branch`, `git remote -v`, `pip freeze`, `pip check` y `python horario_parser.py images`.

### Pruebas realizadas
- `pip check` sin dependencias rotas. El parser devolvió JSON para 6 capturas, con 15, 17, 17, 16, 13 y 18 bloques ocupados respectivamente. Esta prueba verifica compatibilidad de ejecución; la precisión y los reescalados se revisarán en Fase 3.

### Problemas encontrados
- El daemon de Docker rechazó el acceso dentro y fuera del sandbox. El parser devuelve un objeto con `horarios` y estados por color; el plan presenta una lista orientativa. La diferencia la resolverá el adaptador en Fase 3.

### Estado
Implementación inicial completada. Validaciones de entorno registradas en la entrada de cierre.

### Próximo paso
Verificar frontend, proxy, migraciones y CI.

## 2026-11-25 — Fase 0 — Frontend, contenedores y verificación

### Objetivo
Conectar la aplicación con la API, preparar el arranque conjunto y comprobar la infraestructura.

### Cambios implementados
- Frontend React con Vite, rutas, estilos base y una consulta de salud vía TanStack Query.
- Dockerfiles y Compose con PostgreSQL persistente, Nginx, migración previa al arranque y verificaciones de salud.
- GitHub Actions con compilación, lint, formato, pruebas y arranque de Compose.
- README, instrucciones para agentes, seguimiento y decisiones.

### Archivos creados
- `frontend/`, `backend/Dockerfile`, `backend/.dockerignore`, `backend/tests/test_health.py`, `infrastructure/nginx/default.conf`, `docker-compose.yml`, `.github/workflows/ci.yml`, `README.md`, `AGENTS.md` y `docs/`.

### Archivos modificados
- Se completaron `.env.example`, la API y la configuración de pruebas creadas en el bloque inicial.

### Decisiones técnicas
- ADR-001 documenta el proxy de mismo origen, la red privada y el volumen de base de datos.

### Comandos ejecutados
- `npm ci`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build`, `npm audit --audit-level=low`.
- `ruff check .`, `ruff format --check .`, `pytest -m 'integration or not integration'`, `alembic upgrade head`, `alembic current`, `alembic check`.
- `curl` contra el frontend servido por Vite y su proxy de API, `docker compose config -q`, `docker compose up --build --wait` y `git check-ignore`.

### Pruebas realizadas
- Frontend: instalación reproducible, lint y formato correctos, 2 pruebas aprobadas y compilación exitosa. Auditoría npm sin vulnerabilidades en el lockfile final.
- Backend: Ruff y `pip check` correctos. Dos pruebas aprobaron, una con PostgreSQL real.
- PostgreSQL 17.12: la API conectó y Alembic aplicó `0001` desde una base vacía UTF-8. La consulta a través de Vite devolvió HTTP 200.
- Compose y CI: se validó la configuración de Compose y el YAML del workflow. No se verificaron mediante una ejecución completa.

### Problemas encontrados
- npm reportó alertas críticas con Vitest 3. Se actualizó Vitest y sus dependencias compatibles y la auditoría final quedó en cero.
- La instancia local de prueba inicial usaba SQL_ASCII. Se creó una base UTF-8 vacía para verificar las migraciones.
- Starlette emite un aviso de deprecación de HTTPX en TestClient. Las pruebas aprobaron.
- El daemon de Docker rechazó el arranque por permisos del socket, incluso fuera del sandbox. No existe remoto GitHub para verificar el pipeline.
- El checklist maestro y la tabla detallada de infraestructura usan algunos de los mismos IDs para tareas distintas. El seguimiento conserva los IDs del checklist y registra los criterios por separado.

### Estado
Parcialmente completada. El entorno local está verificado y quedan pendientes las comprobaciones de Compose y GitHub Actions.

### Próximo paso
Verificar Compose y CI, y obtener aprobación explícita antes de comenzar la Fase 1.
