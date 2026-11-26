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

## ADR-007 — Procesador externo y revalidación del borrador

- Fecha: 2026-11-25.
- Estado: Adoptada en Fase 3.
- Contexto: El parser devuelve coordenadas ocupadas y debe ejecutar OpenCV sin conservar la captura ni bloquear la base durante el análisis.
- Decisión: Reutilizar `horario_parser.py` desde un proceso Python separado con límites de tiempo, memoria y paralelismo. El adaptador verifica formato, dimensiones y contrato de salida antes de completar las 70 celdas. La API captura la identidad de la membresía y el horario, cierra la transacción, procesa y vuelve a comprobar identidad, sesión y versión antes de persistir.
- Alternativas consideradas: Ejecutar OpenCV en el proceso web o mantener bloqueada la sala durante la extracción.
- Justificación: Limita el impacto de archivos problemáticos y deja disponibles las operaciones de cuenta, sala y horario durante el procesamiento.
- Consecuencias: La aplicación usa `If-Match` con el identificador y la versión para detectar también el borrado y recreación de un horario. El formato recomendado es PNG. La captura se elimina incluso si falla la extracción.
- Archivos afectados: `backend/app/image_processing/`, `backend/app/schedules/` y `frontend/src/features/schedules/`.

## ADR-008 — Superposición calculada desde una consulta consistente

- Fecha: 2026-11-25.
- Estado: Adoptada en Fase 4.
- Contexto: Un resultado completo debe dar simultáneamente los pesos, la cobertura y los pendientes aunque cambien los horarios.
- Decisión: Consultar en una sola sentencia las membresías vigentes y las celdas de horarios confirmados de la sala. La misma consulta comprueba el rol administrativo de quien solicita el resultado.
- Alternativas consideradas: Consultas separadas de miembros y horarios, y una matriz persistida con invalidación.
- Justificación: La sentencia usa una misma vista de PostgreSQL y el cálculo no depende de cachés. Las ediciones y eliminaciones se reflejan al consultar de nuevo.
- Consecuencias: Un borrador, un horario ausente y un horario incompleto no aportan disponibilidad. El mapa y el panel pueden reflejar instantes distintos. La interfaz refresca el mapa si detecta una diferencia al consultar el bloque.
- Archivos afectados: `backend/app/overlap/`, `frontend/src/features/overlap/`.

## ADR-009 — TLS en el proxy y registros sin datos de solicitud

- Fecha: 2026-11-25.
- Estado: Adoptada en Fase 5.
- Contexto: Las sesiones necesitan transporte seguro en producción y los registros deben ayudar a diagnosticar errores sin exponer credenciales.
- Decisión: Terminar TLS en Nginx, mantener PostgreSQL y FastAPI en la red interna y emitir logs JSON con un identificador compartido. La configuración exige que el origen de la aplicación sea HTTPS cuando se configura producción.
- Alternativas consideradas: Exponer FastAPI y resolver HTTPS en cada servicio o registrar solicitudes completas para diagnosticar errores.
- Justificación: Un mismo origen simplifica las cookies. El identificador permite correlacionar solicitudes sin registrar rutas, consultas, cuerpos o cabeceras privadas.
- Consecuencias: El operador aprovisiona y renueva certificado y clave. Las pruebas locales usan certificados temporales. La operación debe configurar la retención de logs y respaldos.
- Archivos afectados: `docker-compose.production.yml`, `infrastructure/nginx/`, `backend/app/core/request_log.py` y `docs/deployment.md`.

## ADR-010 — Migración lógica al cambiar la imagen base de PostgreSQL

- Fecha: 2026-11-25.
- Estado: Adoptada en Fase 5.
- Contexto: La auditoría de las imágenes detectó vulnerabilidades críticas en la base Debian de PostgreSQL y en un binario de la imagen. La imagen Alpine conserva PostgreSQL 17 y usa musl.
- Decisión: Usar `postgres:17-alpine` con un volumen propio. La imagen de SRC sustituye el binario `gosu` afectado por `su-exec` de Alpine y conserva el entrypoint oficial que cambia al usuario `postgres`. Para instalaciones existentes, exportar un respaldo lógico y restaurarlo en el volumen nuevo antes de reabrir el servicio.
- Justificación: La restauración lógica reconstruye los índices con las reglas de ordenamiento de la nueva imagen y conserva el volumen anterior para una reversión controlada.
- Consecuencias: Las instalaciones existentes requieren una ventana de mantenimiento y la validación del respaldo antes del cambio. El procedimiento de despliegue documenta la migración y la reversión.
- Archivos afectados: `docker-compose.yml`, `infrastructure/postgres/Dockerfile`, `.github/workflows/ci.yml` y `docs/deployment.md`.

## ADR-011 — Identidad de Supabase y sesiones de SRC

- Fecha: 2026-11-25.
- Estado: Cambio autorizado por el usuario. Verificación en staging pendiente.
- Contexto: El proyecto nuevo usará Supabase Auth y PostgreSQL administrado. No hay cuentas que migrar. Los permisos por sala y las transferencias al eliminar una cuenta pertenecen a SRC.
- Decisión: FastAPI verifica las credenciales contra Supabase Auth. El perfil usa el UUID de Auth. El correo se consulta en el esquema de identidad y la contraseña queda bajo custodia de Supabase. SRC conserva su cookie opaca y CSRF. El backend elimina perfil, salas según las decisiones del usuario y la identidad dentro de una misma transacción PostgreSQL. El rol `src_app` tiene funciones restringidas para consultar y eliminar la identidad.
- Consecuencias: El registro administrado devuelve 202 y requiere confirmar el correo antes de iniciar sesión. El cambio de dirección se refleja tras la confirmación. El despliegue requiere SMTP, el mismo proyecto para Auth y PostgreSQL, y un ensayo de restauración que incluya ambos esquemas. La eliminación requiere comprobar los permisos y cascadas del esquema Auth del proyecto alojado.
- Archivos afectados: `backend/app/auth/`, `backend/app/users/`, `backend/migrations/versions/0003_supabase_identity.py`, `infrastructure/supabase/permissions.sql` y flujos de registro y perfil del frontend.
