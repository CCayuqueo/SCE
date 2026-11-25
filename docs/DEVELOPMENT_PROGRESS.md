# Estado de desarrollo — SRC V1

## Estado general

- Fase actual: Fase 0 — Configuración e infraestructura.
- Estado: Parcialmente completada.
- Última actualización: 2026-11-25.
- Última tarea completada: pruebas locales de frontend, FastAPI, PostgreSQL y Alembic.
- Próxima tarea pendiente: validar Compose y GitHub Actions, y comprobar el arranque desde un clon.
- Aprobación para avanzar: Pendiente.

Los identificadores de las listas corresponden al checklist maestro §5.2.
La tabla detallada «0.1. Tareas de infraestructura» reutiliza F0-01 a F0-09 con significados distintos. La
validación de Fase 0 se realiza por entregable y por criterio CA0, sin renumerar el plan.

## Fase 0 — Configuración e infraestructura

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

- [ ] F1-01 · Crear modelos y migraciones de las seis tablas.
- [ ] F1-02 · Implementar restricciones y relaciones.
- [ ] F1-03 · Implementar registro y hashing de contraseñas.
- [ ] F1-04 · Implementar login y sesiones.
- [ ] F1-05 · Implementar autorización global y CSRF.
- [ ] F1-06 · Implementar perfil y cambio de contraseña.
- [ ] F1-07 · Implementar previsualización de eliminación.
- [ ] F1-08 · Implementar eliminación y transferencias transaccionales.
- [ ] F1-09 · Crear pantallas Login y Registro.
- [ ] F1-10 · Implementar AuthProvider y rutas protegidas.
- [ ] F1-11 · Crear pantalla Ajustes y confirmaciones.
- [ ] F1-12 · Ejecutar pruebas de autenticación e integridad.

## Fase 2 — Salas, códigos y roles

- [ ] F2-01 · Implementar creación transaccional de salas.
- [ ] F2-02 · Implementar generación segura de códigos.
- [ ] F2-03 · Implementar consulta e ingreso a salas.
- [ ] F2-04 · Implementar dependencias de autorización local.
- [ ] F2-05 · Implementar consulta de miembros.
- [ ] F2-06 · Implementar promoción y revocación de administradores.
- [ ] F2-07 · Implementar transferencia, abandono y cierre de salas.
- [ ] F2-08 · Construir pantalla Salas y formularios.
- [ ] F2-09 · Construir espacio de trabajo y navegación por rol.
- [ ] F2-10 · Construir interfaz de gestión de miembros.
- [ ] F2-11 · Validar concurrencia, permisos y eliminación de cuentas.

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

- Completar las verificaciones de Fase 0 y solicitar aprobación explícita.
