# Verificación previa al lanzamiento

## Resultados locales

- Backend con PostgreSQL 17.12: 39 pruebas pasaron. Incluyen cuentas, permisos,
  concurrencia, formato de capturas, sesiones y eliminación, pesos y logs.
- Cobertura de líneas y ramas: 94 % agregado en los módulos críticos medidos. CI comprueba el umbral de 80 %. El worker de OpenCV se verifica con pruebas funcionales de subproceso.
- Frontend: dos pruebas Vitest, compilación, ESLint y comprobación de formato.
- Playwright: dos pruebas por navegador en Chrome, Firefox y Microsoft Edge 158.0.4370.33. Se ejecutaron contra Nginx
  local con TLS y la configuración de aplicación de producción. Se verificaron
  el flujo de tres cuentas y la navegación móvil por teclado.
- Auditoría de dependencias: npm y los requisitos Python de producción no
  reportaron vulnerabilidades conocidas al ejecutar las comprobaciones.
- Recuperación: se restauró un respaldo no productivo en una base vacía. La
  revisión `0002`, los recuentos y la huella de las 7.630 celdas coincidieron.
- Rendimiento de referencia: p95 de 82,7 ms para 20 superposiciones locales
  con 100 integrantes y 7.000 celdas, medido en Fase 4. En Fase 5, el
  p95 fue de 34,4 ms para 30 consultas autenticadas de perfil y de 818,2 ms
  para las seis cargas PNG. Las dos mediciones usaron FastAPI TestClient,
  PostgreSQL 17.12 por socket local y, para el procesamiento, el subproceso real.
- Respaldo: con `pg_dump` local y el transporte Compose simulado, el script
  generó un archivo válido con permisos `0600` y limpió su temporal después de
  un fallo. Se validaron las unidades de systemd sin activarlas en el servidor.

## Capturas de referencia

Los seis PNG de `images/` se verifican contra coordenadas de ocupación en
`backend/tests/fixtures/schedule_reference.json`. El flujo en navegador usa tres
capturas distintas. Las pruebas agregan una grilla vacía, un recorte incompleto,
un JPEG compatible y archivos inválidos. Los JPEG con pérdida de líneas pueden
ser rechazados aunque correspondan a un archivo JPEG válido.

## Repetir

Desde `backend/`, con `DATABASE_URL` configurada para una base aislada:

```bash
alembic upgrade head
coverage run -m pytest -m 'integration or not integration'
coverage report
alembic check
```

Para el flujo en navegador, inicia un entorno de pruebas y sigue las
[instrucciones del README](../README.md#pruebas-de-flujo-y-producción). La suite
crea datos y elimina cuentas ficticias, por lo que el destino debe ser desechable.
Para un certificado de desarrollo local, `SRC_E2E_LOCAL_TLS=1` permite confiar
en él dentro del contexto de Playwright. En staging se usa el certificado real. Para probar Edge, define
`SRC_E2E_EDGE` con la ruta al ejecutable de Microsoft Edge y ejecuta
`npm run test:e2e -- --project=edge`.

## Resultados en GitHub Actions

[La ejecución 45728893992](https://github.com/CCayuqueo/SCE/actions/runs/45728893992) verificó la
construcción y el arranque con Docker, el parser dentro del contenedor, HTTPS
y cuatro pruebas Playwright en staging desechable. Una copia generada por el
script de respaldo se restauró en una base nueva y sus recuentos coincidieron.
Pasaron 39 pruebas de backend con 94 % de cobertura en los módulos medidos.
Trivy detectó cero vulnerabilidades críticas en las imágenes de frontend,
backend y PostgreSQL.

La [ejecución 45736121907](https://github.com/CCayuqueo/SCE/actions/runs/45736121907)
validó la imagen de Render con 512 MiB y 0,1 CPU. Comprobó el SQL de inicio,
la salud con `src_app`, las rutas de React y las seis capturas. Cada captura
tardó entre 4,39 y 4,50 s. La auditoría de las cuatro imágenes pasó. El
[artefacto SQL](https://github.com/CCayuqueo/SCE/actions/runs/45736121907/artifacts/15078792522)
se generó sin secretos y se aplicó a PostgreSQL efímero.

## Pendiente de lanzamiento

El entorno efímero usa un certificado temporal. Quedan por verificar el dominio,
el respaldo programado y la aceptación con usuarios reales.
