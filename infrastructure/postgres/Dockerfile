FROM postgres:17-alpine

# El entrypoint oficial invoca gosu para iniciar el servidor como postgres.
RUN apk add --no-cache su-exec \
    && ln -sf "$(command -v su-exec)" /usr/local/bin/gosu \
    && test "$(gosu postgres id -un)" = postgres
