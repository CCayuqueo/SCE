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

## 2026-11-25 — Fase 1 — Modelos y migración inicial

### Objetivo
Completar F1-01 y F1-02, correspondientes a F1-B01 a F1-B07. El usuario autorizó iniciar la Fase 1 y guardar avances con commits.

### Cambios implementados
- Modelos SQLAlchemy y migración `0002` para las seis tablas del plan.
- Restricciones de unicidad, rangos, estados, propiedad y eliminación en cascada. La referencia a la membresía del propietario se comprueba al finalizar la transacción.
- Pruebas de integridad con PostgreSQL real e incorporación al job de backend en GitHub Actions.

### Archivos creados
- `backend/app/models.py`, `backend/migrations/versions/0002_esquema_inicial_src.py`, `backend/tests/test_schema.py`.

### Archivos modificados
- `backend/migrations/env.py`, `.github/workflows/ci.yml`, `README.md` y documentos de seguimiento.

### Decisiones técnicas
- ADR-003 documenta la clave foránea diferible y las implicaciones para la futura eliminación de cuentas.

### Comandos ejecutados
- `alembic upgrade head`, `alembic check`, `alembic downgrade 0001`, `pytest -m 'integration or not integration'`, `ruff check .` y `ruff format .`.

### Pruebas realizadas
- Cinco pruebas aprobadas en el backend. PostgreSQL rechazó registros y coordenadas duplicados, estados de propiedad inválidos y la eliminación de un dueño sin resolver su sala. Una transferencia válida conservó la sala y la eliminación del dueño anterior propagó las cascadas.
- En una base temporal PostgreSQL 17.12 se aplicaron las migraciones, se revirtió `0002` y se aplicó de nuevo. `alembic check` no encontró diferencias.
- La infraestructura previa quedó registrada en el commit `4ee7e0c`.

### Problemas encontrados
- Docker continúa sin acceso al daemon. Se usó PostgreSQL por socket local. El workflow modificado está pendiente de ejecución en GitHub.
- TestClient sigue emitiendo el aviso de deprecación de HTTPX registrado en la Fase 0.

### Estado
Bloque de esquema completado y verificado. Fase 1 parcialmente completada.

### Próximo paso
Implementar registro con Argon2id, login, sesiones revocables y CSRF antes de construir el perfil y la eliminación de cuenta.

## 2026-11-25 — Fase 1 — Registro, sesiones y acceso web

### Objetivo
Completar F1-03 a F1-05 y F1-09 a F1-10.

### Cambios implementados
- API de registro, login, recuperación y logout, con Argon2id, cookies HttpOnly y sesiones revocables en PostgreSQL.
- Validación de origen para escrituras, CSRF para operaciones autenticadas y límites de intentos por cuenta e IP.
- Formularios de registro e inicio, restauración al recargar, ruta protegida e invalidación de sesión ante HTTP 401.
- Errores de validación con formato del plan y sin datos ingresados por el usuario.

### Archivos creados
- `backend/app/auth/`, `backend/app/core/errors.py`, `backend/tests/test_auth.py`, `backend/tests/test_rate_limit.py` y `frontend/src/features/auth/`.

### Archivos modificados
- `backend/app/core/config.py`, `backend/app/main.py`, `.env.example`, `docker-compose.yml`, `infrastructure/nginx/default.conf`, entradas del frontend, cliente HTTP y documentación.

### Decisiones técnicas
- ADR-004 documenta cookies opacas, hashes, CSRF recuperable y límites para el proceso web único.

### Comandos y pruebas
- Ruff, ESLint, Prettier, Vitest y compilación TypeScript/Vite completados. Dos pruebas Vitest pasaron.
- Trece pruebas Pytest pasaron con PostgreSQL 17.12, incluidas revocación, expiración, origen, CSRF y límites.
- Prueba temporal con Playwright y Brave sobre Vite, FastAPI y PostgreSQL. Pasaron redirección de ruta privada, registro, recarga, login rechazado, login correcto y logout. La cookie quedó inaccesible a JavaScript y desapareció al cerrar sesión.
- `docker compose config -q` pasó. Sigue pendiente la ejecución del proxy Nginx en contenedores y del workflow en GitHub.

### Problemas encontrados
- La primera prueba de rotación agregó una cookie manual con un dominio distinto al de TestClient. Se corrigió la simulación y se volvió a verificar.
- Se mantiene el aviso de deprecación de HTTPX en TestClient. Los límites de intentos son por proceso, según el despliegue inicial de un solo proceso.

### Estado
Bloque de autenticación completado. Fase 1 parcialmente completada.

### Próximo paso
Implementar perfil, cambio de contraseña, previsualización y eliminación transaccional de cuenta con las pantallas correspondientes.

## 2026-11-25 — Fase 1 — Ajustes, eliminación de cuenta y cierre

### Objetivo
Completar F1-06 a F1-08 y F1-11 a F1-12.

### Cambios implementados
- API y pantalla de perfil con reautenticación para cambiar el correo. Cambio de contraseña que revoca las demás sesiones.
- Vista previa con recuentos y candidatos a sucesor. La recomendación prioriza a los administradores por antigüedad.
- Eliminación transaccional de cuenta, con confirmación explícita, validación de la vista previa, transferencia o cierre y cascadas.
- Pantalla Ajustes y diálogo accesible de revisión y confirmación.

### Archivos creados
- `backend/app/users/`, `backend/tests/test_users.py` y `frontend/src/features/account/`.

### Archivos modificados
- Autenticación y registro de rutas en FastAPI. Cliente HTTP, rutas y estado de sesión en React. README y documentos de seguimiento. Se revisó AGENTS.md y siguen vigentes sus instrucciones.

### Decisiones técnicas
- ADR-005 documenta la protección contra confirmar una vista previa desactualizada mediante ETag e If-Match.

### Comandos y pruebas
- Pytest con PostgreSQL 17.12: 15 pruebas pasaron. Las pruebas nuevas validaron perfil, revocación de otras sesiones, reautenticación, conflictos, transferencia, cierre y conservación de horarios de otros integrantes.
- Playwright temporal con Brave, Vite y FastAPI: edición de perfil, cambio de contraseña y eliminación, incluida la redirección a login y desaparición de la cookie.
- Ruff, ESLint, Prettier, TypeScript/Vite, dos pruebas de Vitest y `alembic check` pasaron.

### Problemas encontrados
- Sigue pendiente la ejecución de Docker y del pipeline de GitHub. Se mantiene el aviso de deprecación de HTTPX en TestClient.

### Estado
Fase 1 completada — Pendiente de aprobación.

### Próximo paso
Fase 2, gestión de salas y roles, tras autorización explícita.

## 2026-11-25 — Fase 2 — Salas, códigos y administración local

### Objetivo
Completar F2-01 a F2-11, tras la autorización explícita de la fase.

### Cambios implementados
- API para creación, ingreso, consulta, administración, roles, abandono, expulsión, transferencia y cierre.
- Códigos criptográficos, reintentos ante colisión, límite de integrantes y permisos por sala. La base serializa escrituras sobre una misma sala.
- Pantallas de listado y detalle con formularios, copia del código, tabla de integrantes y confirmaciones. Las acciones visibles dependen del rol local.

### Archivos creados
- `backend/app/rooms/`, `backend/tests/test_rooms.py` y `frontend/src/features/rooms/`.

### Archivos modificados
- Registro de rutas, autenticación y configuración del backend, rutas y cliente del frontend, `.env.example`, Compose, README y seguimiento técnico. Se revisó AGENTS.md y sus instrucciones siguen vigentes.

### Decisiones técnicas
- ADR-006 define el orden de bloqueos para mantener los permisos y la capacidad bajo concurrencia.

### Pruebas realizadas
- Diecinueve pruebas de backend con PostgreSQL y dos de frontend. Se verificaron colisiones, ingresos concurrentes, permisos por sala, cascadas y eliminación de cuenta mediante datos creados por la API de salas.
- Playwright temporal con Brave, Vite y FastAPI. Tres cuentas verificaron creación, copia del código, ingreso, promoción, aislamiento de roles entre dos salas, abandono, transferencia y cierre.
- Ruff, ESLint, Prettier, TypeScript/Vite, `alembic check` y `docker compose config -q` completados.

### Problemas encontrados
- El arranque completo de Docker y la ejecución en GitHub siguen pendientes. TestClient conserva el aviso de deprecación de HTTPX.

### Estado
Fase 2 completada — Pendiente de aprobación.

### Próximo paso
Fase 3, auditoría e integración del parser y grilla editable, tras autorización explícita.
