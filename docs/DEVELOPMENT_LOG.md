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

## 2026-11-25 — Fase 3 — Extracción determinista y horario editable

### Objetivo
Completar F3-01 a F3-12 tras la autorización explícita de la fase.

### Cambios implementados
- Se reutilizó el parser original. Se auditaron entrada por ruta, JSON de ocupaciones, control de grilla incompleta y ausencia de archivos secundarios.
- Se añadieron validación PNG/JPEG, límites de cuerpo y píxeles, subproceso acotado, directorio temporal privado y normalización a 70 celdas.
- La API persiste borradores, confirma versiones, protege el acceso y descarta resultados si la sesión, membresía o versión cambian durante la extracción.
- Se añadió la grilla de Mi horario, con vista previa, edición, descarte, avisos, confirmación, reemplazo y eliminación.

### Archivos creados
- `backend/app/image_processing/`, `backend/app/schedules/`, `backend/tests/test_image_processing.py`, `backend/tests/test_schedules.py`, `backend/tests/fixtures/schedule_reference.json` y `frontend/src/features/schedules/`.

### Archivos modificados
- Configuración y registro de rutas del backend, Dockerfile, Compose, Nginx y CI. Cliente HTTP, enrutamiento y navegación de sala en frontend. README y seguimiento técnico. Se revisó AGENTS.md.

### Decisiones técnicas
- ADR-007 documenta el subproceso y la revalidación después de extraer. El juego de referencia de las seis capturas se obtuvo leyendo los colores dentro de cada celda en posiciones auditadas, de forma independiente a la salida del parser.

### Pruebas realizadas
- Se verificaron las coordenadas de ocupación de las seis imágenes y los casos de grilla vacía, recorte incompleto, formato no autorizado, píxeles, carga excesiva, salida inválida y limpieza ante timeout.
- Pasaron 33 pruebas de backend con PostgreSQL, dos de frontend, Ruff, ESLint, Prettier, compilación y `alembic check`.
- Playwright temporal verificó vista previa, carga, grilla de 70 celdas, aviso de navegación, descarte, guardado, recarga, reemplazo y eliminación.
- El parser original, medido en el proceso local después de calentarlo, tardó entre 67,0 y 92,5 ms por PNG, sin contar el arranque del subproceso.

### Problemas encontrados
- Las conversiones JPEG 4:2:0 perdieron líneas de la grilla. Una captura JPEG 4:4:4 de alta calidad conservó las coordenadas en la prueba. Se recomienda PNG y se devuelve 422 al no detectar una grilla compatible.
- Se validó la configuración de Compose y el YAML del workflow. La ejecución completa de Docker y GitHub sigue pendiente.

### Estado
Fase 3 completada — Pendiente de aprobación.

### Próximo paso
Fase 4, superposición e inspección de disponibilidad, tras autorización explícita.

## 2026-11-25 — Fase 4 — Superposición e inspección de disponibilidad

### Objetivo
Completar F4-01 a F4-11 tras la autorización de la fase.

### Cambios implementados
- API administrativa con matriz de 70 pesos, cobertura e inspección por bloque a partir de una consulta consistente.
- Mapa de calor, estado sin confirmaciones y listas de ocupados, disponibles y pendientes. Horarios individuales en solo lectura.
- Actualización al entrar, recuperar el foco, pulsar Actualizar o transcurrir 30 segundos con la vista activa.
- Se corrigió la navegación heredada de Mi horario para que también esté visible para miembros regulares.

### Archivos creados
- `backend/app/overlap/`, `backend/tests/test_overlap.py` y `frontend/src/features/overlap/`.

### Archivos modificados
- Registro de rutas backend y frontend, navegación de sala, README y seguimiento. Se revisó AGENTS.md.

### Decisiones técnicas
- ADR-008 documenta la consulta consistente y la reconciliación del panel con la matriz.

### Comandos y pruebas
- Pasaron 36 pruebas Pytest con PostgreSQL 17.12, dos pruebas Vitest, Ruff, ESLint, Prettier, TypeScript/Vite y `alembic check`.
- La prueba matemática dio 2, 3, 0, 1 y 2. Se repitió tras edición, expulsión e ingreso de un usuario pendiente. Una modificación concurrente mostró el estado anterior íntegro hasta confirmar la escritura.
- El p95 fue de 82,7 ms en 20 consultas locales con 100 integrantes confirmados y 7.000 celdas persistidas, usando TestClient y PostgreSQL local.
- Playwright temporal comprobó permisos, carga y confirmación desde un miembro regular, la matriz, el color para 50 %, el panel y el selector individual.
- `docker compose config -q` pasó. Quedan pendientes el arranque completo con Docker y la ejecución remota de CI.

### Problemas encontrados
- La prueba inicial del selector individual no encontró la etiqueta exacta. Se vinculó explícitamente la etiqueta con el control y la repetición pasó.

### Estado
Fase 4 completada — Pendiente de aprobación.

### Próximo paso
Fase 5, Inicio, Guía, pulido y QA, tras autorización explícita.

## 2026-11-25 — Fase 5 — Interfaz, pruebas de lanzamiento y operación

### Objetivo
Preparar la versión para aceptación y despliegue sin publicar ni operar bases reales.

### Cambios implementados
- Inicio público y privado, navegación adaptable, acceso directo a formularios de salas y guía con una captura compatible.
- Suite Playwright registrada en el repositorio y configurada en CI.
- Perfil Compose de producción, HTTPS, límites del proxy, logs con identificador de solicitud y script de respaldo.
- Manuales de API, arquitectura, datos, reglas, pruebas, despliegue y recuperación.

### Archivos creados
- `frontend/src/app/AppShell.tsx`, `frontend/src/features/home/`, `frontend/src/features/guide/`, `frontend/e2e/` y configuración Playwright.
- `docker-compose.production.yml`, configuración de proxy, `infrastructure/scripts/backup-db.sh`, middleware y prueba de logs.
- Manuales en `docs/` y `CHANGELOG.md`.

### Archivos modificados
- Entrada y estilos del frontend, formularios y flujos de sala, dependencias de pruebas, backend, Compose, CI, README y seguimiento. Se revisó AGENTS.md.

### Decisiones técnicas
- ADR-009 documenta el TLS en el proxy y la correlación de logs sin datos privados.

### Comandos y pruebas
- 37 pruebas Pytest, dos de Vitest, Playwright con dos casos en Chrome y dos en Firefox, compilación y controles de formato.
- El flujo íntegro de tres cuentas y la navegación móvil pasaron sobre TLS local. Se comprobó redirección 308 y HSTS con curl.
- Auditorías npm y pip-audit sin vulnerabilidades conocidas en los manifiestos revisados.
- Respaldo PostgreSQL y restauración en una base vacía. Coincidieron revisión, recuentos y huella de 7.630 celdas.
- Configuración Compose validada, incluidos los ajustes de producción. El YAML del workflow y el script de respaldo se validaron localmente.

### Problemas encontrados
- No hay créditos de equipo confirmados ni destino de staging. No se ejecutó la aceptación con usuarios reales.
- El entorno sigue sin acceso al daemon de Docker. Las verificaciones HTTPS usaron Nginx local con un certificado temporal. Pendientes Edge, auditoría de imágenes y ejecución de CI en GitHub.

### Estado
Fase 5 parcialmente completada. Candidata local verificada, publicación pendiente.

### Próximo paso
Confirmar créditos, validar la infraestructura real y realizar la aceptación antes de publicar.

## 2026-11-25 — Fase 5 — Compatibilidad, cobertura y respaldo diario

### Cambios implementados

- Se añadió un proyecto Playwright opcional para Microsoft Edge.
- Se configuró en CI el umbral de 80 % de cobertura de líneas y ramas de los módulos críticos. Se agregaron dos casos de cabeceras PNG y JPEG dañadas antes de decodificar.
- Se añadieron unidades de systemd para el respaldo diario y se documentó su instalación, comprobación y activación.

### Verificaciones

- Edge 158.0.4370.33 pasó ambos escenarios Playwright sobre Nginx y HTTPS local. Con Chrome y Firefox, los dos escenarios están verificados localmente en los tres navegadores.
- Pasaron 39 pruebas de backend con PostgreSQL 17.12 y `alembic check`. Cobertura agregada del 94 % en los módulos críticos medidos. Ruff y la compilación, lint y formato del frontend verificaron los cambios.
- Medición local con TestClient y PostgreSQL por socket: p95 de 34,4 ms para 30 consultas autenticadas de perfil y de 818,2 ms para las seis cargas originales.
- Se validaron las unidades de respaldo sin activarlas. Con pg_dump real y transporte Compose simulado, el script publicó un archivo válido con permisos 0600 y limpió el temporal al fallar.
- Se recuperó la base temporal tras agotar el espacio de `/tmp` durante la extracción de Edge. Se repitieron las verificaciones afectadas.

### Estado

Fase 5 parcialmente completada. El usuario configuró `origin` y renombró la rama a `main`. La consulta remota encontró `main` en `6fc243f` y cero ejecuciones de GitHub Actions. Quedan pendientes Docker, staging con dominio real, respaldo programado activo, créditos confirmados y aceptación con usuarios. Se conserva `main` y se guarda el bloque en una rama local de QA.

## 2026-11-25 — Fase 5 — Verificación de la candidata en GitHub Actions

### Objetivo

Verificar la configuración de lanzamiento desde un checkout de `develop` y ensayar la recuperación de datos en Docker.

### Cambios implementados

- El backend se ejecuta con UID y GID numéricos sin privilegios. Así se corrigió el conflicto con el grupo `src` de la imagen base.
- CI levanta el perfil de producción en un proyecto Compose efímero y restringe los puertos a localhost. Verifica TLS, salud, migraciones, navegación y restauración en una base separada.
- Trivy audita las tres imágenes construidas y devuelve error ante vulnerabilidades críticas. Las imágenes base de Python, Nginx y PostgreSQL se actualizaron después de la primera auditoría.
- PostgreSQL 17 en Alpine usa un volumen nuevo. La documentación explica cómo migrar el volumen Debian anterior con un respaldo lógico (ADR-010).

### Archivos creados

- `.github/scripts/check-staging.sh`, `.github/scripts/audit-images.sh` e `infrastructure/postgres/Dockerfile`.

### Archivos modificados

- `.github/workflows/ci.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `README.md` y documentación de seguimiento, despliegue, pruebas y decisiones.

### Pruebas realizadas

- La [ejecución 45726375485](https://github.com/CCayuqueo/SCE/actions/runs/45726375485) aprobó los trabajos de frontend, backend y Compose. Se verificaron la grilla de las seis capturas dentro de la imagen y el arranque con PostgreSQL.
- La [ejecución 45727454779](https://github.com/CCayuqueo/SCE/actions/runs/45727454779) aprobó el ensayo HTTPS y de restauración. Su auditoría identificó vulnerabilidades críticas en las imágenes base de los tres servicios.
- La [ejecución 45728005133](https://github.com/CCayuqueo/SCE/actions/runs/45728005133) aprobó la restauración y cuatro pruebas Playwright. Trivy dejó de detectar vulnerabilidades críticas en frontend y backend. Reportó CVE-2025-68121 en `gosu`, incluido en la imagen oficial de PostgreSQL Alpine. La imagen de Compose lo sustituye por `su-exec` y conserva el entrypoint y la cuenta `postgres`.
- La [ejecución 45728484583](https://github.com/CCayuqueo/SCE/actions/runs/45728484583) verificó PostgreSQL, los navegadores y la restauración con `su-exec`. La auditoría todavía reportó el binario heredado al reemplazarlo directamente con un enlace. Se agregó una capa explícita de borrado para registrar su eliminación en la imagen.
- La [ejecución 45728893992](https://github.com/CCayuqueo/SCE/actions/runs/45728893992) aprobó los tres trabajos. Pasaron 39 pruebas de backend con 94 % de cobertura, cuatro pruebas Playwright sobre HTTPS y la restauración. Trivy detectó cero vulnerabilidades críticas en las tres imágenes.
- Se comprobaron `bash -n`, `git diff --check` y las configuraciones Compose de desarrollo y producción.

### Estado

F5-09 completada. Fase 5 parcialmente completada hasta confirmar los créditos (F5-02) y realizar la aceptación (F5-10). Los commits de este bloque se publicaron en `develop`.

### Pendientes para el lanzamiento

- Validar en un servidor el certificado del dominio y la ejecución programada del respaldo, confirmar los créditos y hacer la aceptación con usuarios reales. Los ensayos de CI usan cuentas ficticias y un certificado temporal.
