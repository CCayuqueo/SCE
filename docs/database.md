# Base de datos

- `users` tiene correos normalizados únicos y hashes Argon2id.
- `sessions` contiene hashes de sesión y CSRF, con expiración e inactividad.
- `rooms` y `room_members` vinculan cuentas y salas. Cada sala tiene un
  propietario administrador, validado con una clave foránea compuesta diferible.
- `schedules` tiene como máximo un horario por membresía y una versión.
- `schedule_blocks` tiene coordenadas únicas de día (1 a 7) y bloque (1 a 10).

Eliminar una membresía elimina sus horarios y bloques. Eliminar una cuenta
elimina sus sesiones y membresías. La base restringe eliminar a un propietario
mientras conserve alguna sala. La API exige resolver esas salas primero. El
contenido de cada horario confirmado se valida como una matriz completa de
70 celdas en el servicio.

Los cambios se aplican con `alembic upgrade head`. Véase [despliegue](deployment.md)
para la recuperación y [el plan maestro](../SRC_Plan_Maestro_Desarrollo_V1.md)
para el modelo.
