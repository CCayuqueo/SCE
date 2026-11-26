FROM postgres:17-alpine

# El entrypoint oficial invoca gosu para iniciar el servidor como postgres.
RUN rm /usr/local/bin/gosu
RUN apk add --no-cache su-exec \
    && ln -s "$(command -v su-exec)" /usr/local/bin/gosu \
    && test "$(gosu postgres id -un)" = postgres
