FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system src \
    && useradd --system --gid src --no-create-home src
COPY backend/app ./app
COPY backend/alembic.ini .
COPY backend/migrations ./migrations
COPY horario_parser.py .
USER src
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
