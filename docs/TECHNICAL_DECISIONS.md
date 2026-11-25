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
