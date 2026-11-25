# Verificación previa al lanzamiento

## Resultados locales

- Backend con PostgreSQL 17.12: 37 pruebas pasaron. Incluyen cuentas, permisos,
  concurrencia, formato de capturas, sesiones y eliminación, pesos y logs.
- Frontend: dos pruebas Vitest, compilación, ESLint y comprobación de formato.
- Playwright: dos pruebas en Chrome y dos en Firefox. Se ejecutaron contra Nginx
  local con TLS y la configuración de aplicación de producción. Se verificaron
  el flujo de tres cuentas y la navegación móvil por teclado.
- Auditoría de dependencias: npm y los requisitos Python de producción no
  reportaron vulnerabilidades conocidas al ejecutar las comprobaciones.
- Recuperación: se restauró un respaldo no productivo en una base vacía. La
  revisión `0002`, los recuentos y la huella de las 7.630 celdas coincidieron.
- Rendimiento de referencia: p95 de 82,7 ms para 20 superposiciones locales
  con 100 integrantes y 7.000 celdas, medido en Fase 4.

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
pytest -m 'integration or not integration'
alembic check
```

Para el flujo en navegador, inicia un entorno de pruebas y sigue las
[instrucciones del README](../README.md#pruebas-de-flujo-y-producción). La suite
crea datos y elimina cuentas ficticias, por lo que el destino debe ser desechable.
Para un certificado de desarrollo local, `SRC_E2E_LOCAL_TLS=1` permite confiar
en él dentro del contexto de Playwright. En staging se usa el certificado real.

## Pendiente de lanzamiento

Quedan por verificar Edge, la ejecución completa de Docker y GitHub Actions,
las imágenes de producción, el dominio y respaldo programado en staging y la
aceptación con usuarios reales. La prueba local de TLS usa un certificado
temporal y no sustituye la validación del dominio público.
