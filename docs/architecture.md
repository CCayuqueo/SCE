# Arquitectura

Nginx sirve React y envía `/api/` a FastAPI en el mismo origen. FastAPI usa
SQLAlchemy y PostgreSQL para cuentas, sesiones revocables, membresías y horarios.
Alembic versiona el esquema. El procesador OpenCV corre como subproceso acotado y
solo entrega los bloques detectados. FastAPI normaliza y valida las 70 celdas
antes de persistir un borrador.

`backend/app/` separa autenticación, cuentas, salas, horarios, procesamiento e
inspección de disponibilidad. La superposición lee membresías y horarios
confirmados con una vista consistente de PostgreSQL. React utiliza TanStack
Query y maneja las ediciones de horario de forma local hasta su confirmación.

Consulta [decisiones técnicas](TECHNICAL_DECISIONS.md) y [despliegue](deployment.md).
