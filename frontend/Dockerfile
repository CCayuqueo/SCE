FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:1.30.8-alpine
RUN apk upgrade --no-cache
COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY infrastructure/nginx/00-src-log.conf /etc/nginx/conf.d/00-src-log.conf
COPY infrastructure/nginx/src.locations /etc/nginx/src.locations
COPY --from=build /app/dist /usr/share/nginx/html
