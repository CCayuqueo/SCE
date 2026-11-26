#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_ACTIONS:?Se ejecuta en un runner de GitHub Actions aislado}"
: "${RUNNER_TEMP:?Directorio temporal del runner}"
: "${COMPOSE_PROJECT_NAME:?Proyecto de prueba obligatorio}"

if [[ "$GITHUB_ACTIONS" != true || "$COMPOSE_PROJECT_NAME" != src_ci_* ]]; then
    echo "La verificación solo se ejecuta sobre el proyecto Compose efímero de CI." >&2
    exit 1
fi

staging="$(mktemp -d "$RUNNER_TEMP/src-staging.XXXXXX")"
export APP_ORIGIN=https://localhost
export SRC_TLS_DIR="$staging/tls"
mkdir -m 700 "$SRC_TLS_DIR"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=localhost \
    -addext subjectAltName=DNS:localhost \
    -keyout "$SRC_TLS_DIR/tls.key" -out "$SRC_TLS_DIR/tls.crt" 2>"$staging/openssl.log"
cat > "$staging/loopback.yml" <<'YAML'
services:
  frontend:
    ports: !override
      - "127.0.0.1:80:80"
      - "127.0.0.1:443:443"
YAML

docker compose down --volumes
files=(-f docker-compose.yml -f docker-compose.production.yml -f "$staging/loopback.yml")
docker compose "${files[@]}" up --no-build --wait --wait-timeout 120

curl --fail --silent --show-error --dump-header "$staging/http.headers" --output /dev/null http://localhost/
grep -qi '^location: https://localhost/' "$staging/http.headers"
grep -q '^HTTP/1.1 308 ' "$staging/http.headers"
curl --fail --silent --show-error --cacert "$SRC_TLS_DIR/tls.crt" \
    --dump-header "$staging/https.headers" "$APP_ORIGIN/api/v1/health/ready" > "$staging/health.json"
grep -qi '^strict-transport-security:' "$staging/https.headers"
grep -q '"status":"ok"' "$staging/health.json"
docker compose "${files[@]}" exec -T backend alembic check
test "$(docker compose "${files[@]}" exec -T backend id -u)" -ne 0

(
    cd frontend
    SRC_E2E_URL="$APP_ORIGIN" SRC_E2E_LOCAL_TLS=1 npm run test:e2e
)

backup="$(bash infrastructure/scripts/backup-db.sh "$staging/backups" "${files[@]}")"
docker compose "${files[@]}" exec -T database sh -ec '
    createdb -U "$POSTGRES_USER" src_ci_restore
    pg_restore --exit-on-error --no-owner --no-privileges -U "$POSTGRES_USER" -d src_ci_restore
' < "$backup"

query='SELECT version_num, (SELECT count(*) FROM users), (SELECT count(*) FROM rooms), (SELECT count(*) FROM room_members), (SELECT count(*) FROM schedules), (SELECT count(*) FROM schedule_blocks) FROM alembic_version'
original="$(docker compose "${files[@]}" exec -T database sh -ec 'psql -XAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"' -- "$query")"
restored="$(docker compose "${files[@]}" exec -T database sh -ec 'psql -XAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d src_ci_restore -c "$1"' -- "$query")"
test -n "$original"
test "$original" = "$restored"
echo "Staging efímero: HTTPS, migraciones, Playwright y restauración verificados."
