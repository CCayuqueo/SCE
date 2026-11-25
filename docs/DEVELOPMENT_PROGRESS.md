# Estado de desarrollo — SRC V1

## Estado general

- Fase actual: Fase 2 — Gestión de salas, códigos únicos y roles locales.
- Estado: Completada — Pendiente de aprobación.
- Última actualización: 2026-11-25.
- Última tarea completada: salas, membresías, roles, transferencias y verificación integral.
- Próxima tarea pendiente: Fase 3 — Procesamiento de imágenes y horarios, tras autorización.
- Aprobación para avanzar: Fase 2 autorizada explícitamente. Fase 3 pendiente.

Los identificadores de las listas corresponden al checklist maestro §5.2.
La tabla detallada «0.1. Tareas de infraestructura» reutiliza F0-01 a F0-09 con significados distintos. La
validación de Fase 0 se realiza por entregable y por criterio CA0, sin renumerar el plan.

## Fase 0 — Configuración e infraestructura

El usuario autorizó iniciar Fase 1. Continúan pendientes el arranque con Docker, la verificación desde un clon y la ejecución de GitHub Actions.

- [ ] F0-01 · Crear repositorio y estrategia de ramas.
- [x] F0-02 · Inicializar React, TypeScript y Vite.
- [x] F0-03 · Inicializar FastAPI y arquitectura modular.
- [x] F0-04 · Configurar PostgreSQL y Alembic.
- [ ] F0-05 · Crear Dockerfiles y Docker Compose.
- [x] F0-06 · Configurar variables de entorno y secretos.
- [ ] F0-07 · Implementar proxy, conexión API y health checks.
- [ ] F0-08 · Configurar linters, testing y GitHub Actions.
- [ ] F0-09 · Documentar instalación y ejecución.

## Fase 1 — Base de datos y autenticación

- [x] F1-01 · Crear modelos y migraciones de las seis tablas.
- [x] F1-02 · Implementar restricciones y relaciones.
- [x] F1-03 · Implementar registro y hashing de contraseñas.
- [x] F1-04 · Implementar login y sesiones.
- [x] F1-05 · Implementar autorización global y CSRF.
- [x] F1-06 · Implementar perfil y cambio de contraseña.
- [x] F1-07 · Implementar previsualización de eliminación.
- [x] F1-08 · Implementar eliminación y transferencias transaccionales.
- [x] F1-09 · Crear pantallas Login y Registro.
- [x] F1-10 · Implementar AuthProvider y rutas protegidas.
- [x] F1-11 · Crear pantalla Ajustes y confirmaciones.
- [x] F1-12 · Ejecutar pruebas de autenticación e integridad.

## Fase 2 — Salas, códigos y roles

- [x] F2-01 · Implementar creación transaccional de salas.
- [x] F2-02 · Implementar generación segura de códigos.
- [x] F2-03 · Implementar consulta e ingreso a salas.
- [x] F2-04 · Implementar dependencias de autorización local.
- [x] F2-05 · Implementar consulta de miembros.
- [x] F2-06 · Implementar promoción y revocación de administradores.
- [x] F2-07 · Implementar transferencia, abandono y cierre de salas.
- [x] F2-08 · Construir pantalla Salas y formularios.
- [x] F2-09 · Construir espacio de trabajo y navegación por rol.
- [x] F2-10 · Construir interfaz de gestión de miembros.
- [x] F2-11 · Validar concurrencia, permisos y eliminación de cuentas.

### Criterios de aceptación de Fase 2

| ID | Estado | Evidencia |
|---|---|---|
| CA2-01 | Verificado | Creación autenticada por API y navegador. |
| CA2-02 | Verificado | Colisión simulada en una tabla real, reintento con código distinto. |
| CA2-03 | Verificado | Creador con rol efectivo de propietario y membresía de administrador. |
| CA2-04 | Verificado | Ingreso por código válido en API y navegador. |
| CA2-05 | Verificado | Código inexistente devuelve 404 y deja la lista vacía. |
| CA2-06 | Verificado | Ingreso repetido idempotente y capacidad respetada bajo concurrencia. |
| CA2-07 | Verificado | Un administrador promovió al tercer integrante. |
| CA2-08 | Verificado | Miembro regular recibió 403 al intentar promover. |
| CA2-09 | Verificado | La misma cuenta fue administradora en Sala A y miembro en Sala B. |
| CA2-10 | Verificado | Acceso externo y referencias a membresías de otras salas devuelven 404. |
| CA2-11 | Verificado | Transferencia y rol del propietario anterior comprobados por API y navegador. |
| CA2-12 | Verificado | Abandono, expulsión y cierre eliminaron horarios y bloques dependientes. |

## Fase 3 — Procesamiento de imágenes y horarios

- [ ] F3-01 · Auditar script existente y sus dependencias.
- [ ] F3-02 · Crear conjunto de capturas de prueba.
- [ ] F3-03 · Definir contrato del procesador y adaptador.
- [ ] F3-04 · Implementar worker y límites de ejecución.
- [ ] F3-05 · Implementar validación y limpieza de archivos.
- [ ] F3-06 · Implementar normalización de 70 celdas.
- [ ] F3-07 · Implementar endpoint de carga.
- [ ] F3-08 · Implementar consultas, edición y versiones.
- [ ] F3-09 · Construir componente reutilizable de grilla.
- [ ] F3-10 · Construir interfaz de carga y corrección.
- [ ] F3-11 · Implementar guardado, descarte y manejo de errores.
- [ ] F3-12 · Ejecutar pruebas del parser y del flujo completo.

## Fase 4 — Motor de superposición

- [ ] F4-01 · Implementar recuperación consistente de horarios.
- [ ] F4-02 · Implementar algoritmo de pesos.
- [ ] F4-03 · Implementar métricas de cobertura y disponibilidad.
- [ ] F4-04 · Implementar endpoint consolidado.
- [ ] F4-05 · Implementar endpoint de detalle por celda.
- [ ] F4-06 · Implementar consulta individual de horarios.
- [ ] F4-07 · Construir mapa de calor reutilizable.
- [ ] F4-08 · Construir selector de miembros y vista individual.
- [ ] F4-09 · Construir panel de inspección de bloques.
- [ ] F4-10 · Implementar actualización e invalidación de datos.
- [ ] F4-11 · Verificar pesos, permisos y rendimiento.

## Fase 5 — Inicio, Guía, pulido y QA

- [ ] F5-01 · Construir presentación pública y privada de SRC.
- [ ] F5-02 · Incorporar equipo desarrollador.
- [ ] F5-03 · Finalizar barra lateral y layout adaptable.
- [ ] F5-04 · Construir Guía / Cómo usar.
- [ ] F5-05 · Unificar estilos y estados visuales.
- [ ] F5-06 · Verificar accesibilidad y diseño responsive.
- [ ] F5-07 · Automatizar pruebas E2E.
- [ ] F5-08 · Ejecutar pruebas de seguridad y concurrencia.
- [ ] F5-09 · Preparar despliegue, HTTPS y respaldos.
- [ ] F5-10 · Ejecutar pruebas de aceptación y documentar release.
### Criterios de aceptación de Fase 0

| ID | Estado | Evidencia |
|---|---|---|
| CA0-01 | Pendiente | README disponible y recorrido local comprobado en este checkout. Falta verificar desde un clon con Docker. |
| CA0-02 | Pendiente | Compose acepta la configuración. El daemon rechaza el arranque. |
| CA0-03 | Verificado localmente | Vite sirvió la aplicación y su proxy devolvió la respuesta de FastAPI. La ruta mediante Nginx queda incluida en la verificación de Compose. |
| CA0-04 | Verificado | El endpoint de disponibilidad respondió 200 con PostgreSQL 17.12 y 503 cuando la base no estaba disponible. |
| CA0-05 | Verificado | `alembic upgrade head` desde una base vacía aplicó `0001`. `alembic check` confirmó que no había operaciones pendientes. |
| CA0-06 | Pendiente | YAML válido y compilación y pruebas ejecutadas localmente. Falta una ejecución en GitHub Actions. |
| CA0-07 | Verificado en los archivos revisados | `.env` está ignorado, la plantilla no incluye contraseña y no se detectaron claves o tokens en el árbol revisado. |

## Problemas pendientes

- Docker instalado, pero el usuario del entorno carece de acceso al daemon.
- No hay remoto GitHub configurado.

## Dependencias pendientes

- Acceso a un entorno Docker y al repositorio GitHub de destino.

## Pruebas pendientes

- Arranque de Compose, validación de Nginx, prueba del parser en el contenedor y ejecución de GitHub Actions.

## Próximos pasos

- Iniciar la Fase 3 cuando esté autorizada explícitamente.
- Completar las verificaciones pendientes de infraestructura cuando el entorno lo permita.
