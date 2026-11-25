# Decisiones técnicas — SRC V1

## ADR-001 — Un proxy, una API y una base de datos

- Fecha: 2026-11-25.
- Estado: Adoptada para la Fase 0 según el plan maestro.
- Contexto: El plan define un monolito modular con frontend desacoplado y exige un entorno local reproducible.
- Decisión: Servir React con Nginx, enrutar `/api/` a FastAPI y mantener PostgreSQL en la red de Compose con un volumen persistente. En desarrollo sin Docker, Vite ofrece el mismo prefijo.
- Alternativas consideradas: Exponer puertos de API y base, o exigir CORS entre frontend y API.
- Justificación: Un mismo origen reduce configuración y permite usar el modelo de sesiones previsto. Mantener internos los servicios limita la exposición.
- Consecuencias: Solo el proxy se publica en localhost por defecto. El despliegue público con HTTPS se configura en su fase.
- Archivos afectados: `docker-compose.yml`, `infrastructure/nginx/default.conf`, `frontend/vite.config.ts`.

## ADR-002 — Revisión base de Alembic separada del esquema de negocio

- Fecha: 2026-11-25.
- Estado: Adoptada para la Fase 0 según el plan maestro.
- Contexto: CA0-05 exige ejecutar migraciones desde una base vacía. El esquema de las seis tablas corresponde a la Fase 1.
- Decisión: Usar una revisión inicial sin DDL de negocio y aplicar las migraciones antes de arrancar la API en Compose.
- Alternativas consideradas: Incorporar los modelos en Fase 0 o usar creación automática de tablas al iniciar.
- Justificación: Valida el acceso a PostgreSQL y la infraestructura de migraciones sin adelantar el esquema.
- Consecuencias: La primera migración funcional deberá descender de `0001`. La Fase 1 deberá verificar restricciones y cascadas con PostgreSQL real.
- Archivos afectados: `backend/migrations/`, `backend/alembic.ini`, `docker-compose.yml`.

## ADR-003 — La base de datos garantiza la membresía del propietario

- Fecha: 2026-11-25.
- Estado: Adoptada según el plan maestro.
- Contexto: Las salas conservadas deben tener un propietario que también sea administrador local.
- Decisión: Aplicar la clave foránea compuesta `fk_room_owner_membership` al finalizar la transacción. La clave directa al usuario propietario usa `ON DELETE RESTRICT`.
- Alternativas consideradas: Validar la membresía exclusivamente en FastAPI o propagar la eliminación del usuario propietario a la sala.
- Justificación: PostgreSQL verifica la coherencia incluso ante escrituras fuera de FastAPI. El carácter diferible permite crear una sala y su membresía en la misma transacción.
- Consecuencias: Para eliminar al propietario, el servicio deberá transferir la sala a una membresía administradora o cerrar la sala explícitamente antes de eliminar al usuario. La capa de servicio verificará que un horario confirmado contenga 70 celdas.
- Archivos afectados: `backend/app/models.py` y `backend/migrations/versions/0002_esquema_inicial_src.py`.

## ADR-004 — Sesión opaca revocable y CSRF recuperable

- Fecha: 2026-11-25.
- Estado: Adoptada según el plan maestro.
- Contexto: SRC necesita invalidar sesiones desde PostgreSQL y recuperar el token CSRF tras recargar.
- Decisión: Usar una cookie opaca aleatoria y guardar sus hashes SHA-256 en PostgreSQL. El servidor deriva el token CSRF mediante HMAC con la cookie como clave y un mensaje fijo exclusivo de SRC. Guarda el hash del CSRF y valida las escrituras con token y origen.
- Alternativas consideradas: JWT de larga vida, guardar el token CSRF en texto plano o rotarlo en cada consulta de sesión.
- Justificación: Revocación inmediata, sin almacenar tokens reutilizables en PostgreSQL. Una consulta de sesión recupera el token esperado sin invalidar otras pestañas.
- Consecuencias: El cliente debe consultar `/auth/me` para recuperar la sesión y enviar `X-CSRF-Token` en escrituras autenticadas. Los límites de intentos por cuenta e IP viven en la memoria del proceso y se reinician con él. Si se habilitan réplicas, deberán compartir un mecanismo de límite. En Compose, Nginx reemplaza el encabezado de dirección IP antes de enviarlo a FastAPI por la red privada.
- Archivos afectados: `backend/app/auth/`, `infrastructure/nginx/default.conf` y `docker-compose.yml`.

## ADR-005 — Confirmación de eliminación vinculada a la vista previa

- Fecha: 2026-11-25.
- Estado: Adoptada dentro de la Fase 1.
- Contexto: El plan exige detectar cambios en el impacto de la eliminación desde que el usuario lo revisó.
- Decisión: Representar el estado visible de la vista previa con un `ETag` y exigirlo en `If-Match`. En la transacción se bloquean al usuario, sus salas y las membresías candidatas, se reconstruye la vista y se revalidan las decisiones.
- Alternativas consideradas: Comparar solo la lista de decisiones o guardar una copia temporal de cada vista previa.
- Justificación: La versión detecta cambios incluso cuando las decisiones siguen teniendo una forma válida y mantiene el cuerpo JSON definido por el plan.
- Consecuencias: Un cambio o una decisión inválida devuelve `409`. El frontend vuelve a mostrar la vista previa. La fase de salas deberá respetar el orden de bloqueo al modificar su propiedad y membresías.
- Archivos afectados: `backend/app/users/`, `frontend/src/features/account/`.

## ADR-006 — Serialización de cambios de membresía por sala

- Fecha: 2026-11-25.
- Estado: Adoptada en Fase 2.
- Contexto: El ingreso simultáneo debe respetar capacidad y unicidad. Las decisiones de rol deben seguir vigentes hasta confirmar una escritura.
- Decisión: Bloquear la fila de la sala durante el ingreso o escritura y volver a consultar el permiso antes de actuar. El usuario autenticado se bloquea sin bloquear referencias de clave foránea.
- Alternativas consideradas: Contar integrantes sin bloqueo o usar un bloqueo global.
- Justificación: El bloqueo local serializa cambios de una sala sin detener operaciones de otras salas. Las restricciones existentes siguen siendo la garantía final.
- Consecuencias: Las futuras operaciones que cambien membresías deben seguir el orden usuario, sala y membresía y respetar las restricciones diferibles.
- Archivos afectados: `backend/app/rooms/` y `backend/app/auth/dependencies.py`.
