#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_ACTIONS:?Se ejecuta en un runner aislado de GitHub Actions}"
: "${COMPOSE_PROJECT_NAME:?Proyecto Compose de CI}"
: "${RUNNER_TEMP:?Directorio temporal de CI}"
[[ "$GITHUB_ACTIONS" == true && "$COMPOSE_PROJECT_NAME" == src_ci_* ]]

image="$COMPOSE_PROJECT_NAME-render"
container="$COMPOSE_PROJECT_NAME-render-check"
bootstrap="$RUNNER_TEMP/src-supabase-bootstrap.sql"
docker build -f backend/Dockerfile -t "$image" .
docker run --rm -e DATABASE_URL=postgresql+psycopg://placeholder@localhost/postgres \
    "$image" alembic upgrade head --sql > "$bootstrap"
cat infrastructure/supabase/permissions.sql >> "$bootstrap"

docker compose exec -T database sh -eu -c '
    createdb -U "$POSTGRES_USER" src_render_test
    psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d src_render_test
' <<'SQL'
CREATE SCHEMA auth;
CREATE TABLE auth.users (
    id uuid PRIMARY KEY, email text UNIQUE, email_confirmed_at timestamptz,
    deleted_at timestamptz, banned_until timestamptz
);
CREATE ROLE anon;
CREATE ROLE authenticated;
CREATE ROLE service_role;
SQL
docker compose exec -T database sh -eu -c '
    psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d src_render_test
' < "$bootstrap"
docker compose exec -T database sh -eu -c '
    psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d src_render_test \
        -v password="$POSTGRES_PASSWORD"
' <<'SQL'
ALTER ROLE src_app LOGIN PASSWORD :'password';
SQL

cleanup() {
    docker logs --tail 35 "$container" || true
    docker rm -f "$container" >/dev/null || true
}
trap cleanup EXIT
export DATABASE_URL="postgresql+psycopg://src_app:${POSTGRES_PASSWORD:?}@database:5432/src_render_test"
docker run -d --name "$container" --network "${COMPOSE_PROJECT_NAME}_default" \
    --memory 512m --memory-swap 512m --cpus 0.1 -p 127.0.0.1:10080:10080 \
    -e DATABASE_URL -e APP_ENV=test -e PORT=10080 \
    -e RENDER_EXTERNAL_URL=https://render-ci.example.com \
    -e SUPABASE_URL=https://auth-ci.example.com -e SUPABASE_PUBLISHABLE_KEY=ci-only-placeholder \
    -v "$PWD/images:/parser/images:ro" "$image"

origin=http://127.0.0.1:10080
curl -fsS --retry 15 --retry-connrefused --retry-delay 2 --max-time 5 \
    "$origin/api/v1/health/ready" | grep '"status":"ok"'
test "$(docker exec "$container" id -u)" -ne 0
for route in / /login /register /app/salas; do
    curl -fsS "$origin$route" | grep '<title>SRC</title>'
done
curl -fsSI "$origin/login" | grep -i '^strict-transport-security: max-age=31536000'
asset="$(curl -fsS "$origin/" | sed -nE 's/.*src="(\/assets\/[^\"]+\.js)".*/\1/p')"
test -n "$asset"
curl -fsSI "$origin$asset" | grep -i '^cache-control: public, max-age=31536000, immutable'
for route in /api/v1/no-existe /assets/no-existe.js /docs; do
    test "$(curl -sS -o /dev/null -w '%{http_code}' "$origin$route")" = 404
done
test "$(curl -sS -o /dev/null -w '%{http_code}' "$origin/api/v1/auth/me")" = 401

docker exec -i "$container" python - <<'PY'
from pathlib import Path
from time import perf_counter

from app.core.config import Settings
from app.image_processing.adapter import ImageProcessor

processor = ImageProcessor(Settings())
counts = []
for capture in sorted(Path('/parser/images').glob('*.png')):
    started = perf_counter()
    counts.append(sum(cell.is_occupied for cell in processor.process(capture.read_bytes())))
    print(f'Captura {len(counts)}: {perf_counter() - started:.2f} s')
assert counts == [15, 17, 17, 16, 13, 18], counts
PY
