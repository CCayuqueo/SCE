#!/usr/bin/env bash
set -euo pipefail

scan="$(mktemp -d "${RUNNER_TEMP:?}/src-image-audit.XXXXXX")"
mkdir "$scan/cache"
images="$(docker compose config --images)"
test -n "$images"
status=0
while IFS= read -r image; do
    echo "::group::Vulnerabilidades críticas en $image"
    docker save "$image" -o "$scan/image.tar"
    if ! docker run --rm \
        -v "$scan/image.tar:/tmp/image.tar:ro" \
        -v "$scan/cache:/tmp/cache" \
        aquasec/trivy:0.76.2 image --input /tmp/image.tar --cache-dir /tmp/cache \
        --scanners vuln --severity CRITICAL --exit-code 1; then
        status=1
    fi
    unlink "$scan/image.tar"
    echo "::endgroup::"
done <<< "$images"
exit "$status"
