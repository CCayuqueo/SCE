#!/bin/sh
set -eu

: "${DATABASE_URL:?Configura DATABASE_URL para el rol src_app}"
: "${SUPABASE_URL:?Configura SUPABASE_URL}"
: "${SUPABASE_PUBLISHABLE_KEY:?Configura SUPABASE_PUBLISHABLE_KEY}"
export APP_ORIGIN="${APP_ORIGIN:-${RENDER_EXTERNAL_URL:?Configura APP_ORIGIN}}"

exec uvicorn app.render:app --host 0.0.0.0 --port "${PORT:-10000}" \
    --no-access-log --no-server-header
