# API

Los contratos ejecutables están disponibles en `/openapi.json` y la
documentación de desarrollo en `/docs` al iniciar FastAPI localmente.

- `/api/v1/auth`: registro, acceso, consulta de sesión y cierre.
- `/api/v1/users/me`: perfil, contraseña, vista previa y eliminación de cuenta.
- `/api/v1/rooms`: creación, ingreso, consulta, membresías y roles.
- `/api/v1/rooms/{room_id}/schedules/me`: carga multipart, edición, consulta y eliminación del horario propio.
- `/api/v1/rooms/{room_id}/members/{member_id}/schedule`: solo horarios confirmados para administración.
- `/api/v1/rooms/{room_id}/overlap`: pesos consolidados e inspección por bloque para propietarios y administradores.
- `/api/v1/health`: proceso activo y disponibilidad de PostgreSQL.

Las operaciones privadas requieren la cookie de sesión. Las escrituras
autenticadas validan `Origin` y `X-CSRF-Token`. El guardado del horario exige la
versión conocida y admite el identificador con `If-Match`. Para eliminar una
cuenta, envía el `ETag` de la vista previa como `If-Match`. Los conflictos
requieren repetir la consulta antes de enviar los cambios otra vez.

Con Supabase Auth, `POST /api/v1/auth/register` devuelve `202` y pide verificar
el correo antes de iniciar sesión. La respuesta es la misma si el proveedor
acepta la solicitud o identifica un correo ya registrado. Cuando se solicita un
cambio de correo, `PATCH /api/v1/users/me` devuelve el correo vigente. Al
confirmar el cambio, la siguiente consulta de sesión devuelve el nuevo.
