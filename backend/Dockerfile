FROM node:24-bookworm-slim AS web-build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim-trixie AS backend

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/alembic.ini .
COPY backend/migrations ./migrations
COPY horario_parser.py .
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM backend AS render
ENV APP_ENV=staging IMAGE_PROCESSING_CONCURRENCY=1 IMAGE_PROCESSING_TIMEOUT_SECONDS=30
COPY --from=web-build /web/dist /app/web
COPY infrastructure/render/start.sh /app/render-start.sh
CMD ["sh", "/app/render-start.sh"]
