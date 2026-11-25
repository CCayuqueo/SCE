#!/usr/bin/env bash
set -euo pipefail

destination=${1:?Indica un directorio de respaldos}
shift
umask 077
mkdir -p -- "$destination"
backup="$destination/src-$(date -u +%Y%m%dT%H%M%SZ).dump"
temporary="$(mktemp -- "$destination/.src-backup.XXXXXX")"
trap 'unlink -- "$temporary" 2>/dev/null || true' EXIT

docker compose "$@" exec -T database sh -c 'pg_dump -Fc --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$temporary"
test -s "$temporary"
# No se sobrescribe un respaldo anterior si coinciden los segundos.
ln -- "$temporary" "$backup"
printf '%s\n' "$backup"
