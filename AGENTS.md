# Instrucciones de desarrollo de SRC

SRC analiza la disponibilidad horaria académica en salas con permisos locales. El [plan maestro](SRC_Plan_Maestro_Desarrollo_V1.md) define su alcance, arquitectura y criterios de aceptación.

## Antes de trabajar

Lee este archivo, el plan maestro, `docs/DEVELOPMENT_PROGRESS.md`, `docs/DEVELOPMENT_LOG.md`, `docs/TECHNICAL_DECISIONS.md` y `README.md`, en ese orden. Revisa `git status` e inspecciona el código de la tarea pendiente antes de editar. Conserva los cambios del usuario.

Trabaja en una fase a la vez y ejecuta cada tarea según sus dependencias. Registra resultados reales al completar cada bloque significativo y antes de terminar la sesión. Mantén actualizado el README y conserva el historial de la bitácora y los ADR. Una fase terminada queda pendiente de aprobación explícita. Detente y pide autorización antes de iniciar la siguiente. No hagas commits, pushes, merges ni operaciones destructivas sin autorización.

## Arquitectura y convenciones

- `frontend/`: React, TypeScript, Vite, React Router, Tailwind CSS y TanStack Query. Usa TypeScript estricto, componentes simples y solicitudes de API del mismo origen.
- `backend/`: monolito modular en FastAPI con Pydantic, SQLAlchemy, Alembic y PostgreSQL. Separa rutas, lógica de negocio y persistencia. Usa tipado, Ruff y Pytest.
- `infrastructure/nginx/`: proxy inverso. Docker Compose mantiene la API y PostgreSQL en la red privada.
- `horario_parser.py`: parser existente en OpenCV y NumPy. Preserva su contrato y usa un adaptador en Fase 3. No utilices IA, OCR externo ni aprendizaje automático.
- Vitest, Pytest y Playwright forman parte de la estrategia de pruebas del plan. Justifica y solicita aprobación para cambios de stack o dependencias importantes ajenas al plan.

## Seguridad y alcance

Valida entradas en frontend y backend, y aplica permisos de sala en el backend. Mantén secretos fuera de Git, documenta variables con `.env.example` y nunca guardes contraseñas en texto plano. Para capturas, valida tipo y tamaño, limita recursos y elimina temporales. Las eliminaciones deben preservar la integridad referencial. No implementes eventos, reuniones, invitaciones, ayudantías, evaluaciones ni administración global.

## Comandos de la Fase 0

- Docker desde la raíz: `docker compose up --build` con la configuración del README.
- Frontend desde `frontend/`: `npm ci`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build`.
- Backend desde `backend/`: `pip install -r requirements-dev.txt`, `ruff check .`, `ruff format --check .`, `pytest`. Con PostgreSQL de pruebas y `DATABASE_URL`, usa `alembic upgrade head` y `pytest -m integration`.
