# Run Shellui Marketplace

Shellui Marketplace serves the app catalog at `/api/apps` and install stats at `/api/apps/<slug>/install`. Use this page to run the `shellui/marketplace-service` image. Every listing in 0.9 is free.

## What is inside the image

The entrypoint starts as root, prepares `/app/data`, and runs the app as `appuser`.

| Item | Value |
| --- | --- |
| Base | `python:3.14-slim` |
| Listen port | `8000` |
| Entrypoint | `/app/tools/docker-entrypoint.sh` |
| App processes | `appuser` |
| Volume | `/app/data` (SQLite and filesystem media) |

Node.js 22 builds the CSS during the image build. The default command is `web`: migrate, seed the catalog, then Gunicorn. The image sets `DEBUG=false` and `STORAGE_BACKEND=filesystem`.

## Start a container

Replace `your_secret_key_here` with a key of at least 50 characters. An empty `POSTGRES_DATABASE_URL` uses SQLite on the volume. Set `REDIS_URL` to a Redis URL the container can reach.

```bash
docker run --rm -p 8000:8000 \
  -v marketplace-data:/app/data \
  -e SECRET_KEY=your_secret_key_here \
  -e DEBUG=false \
  -e ALLOWED_HOSTS=market.example.com \
  -e CSRF_TRUSTED_ORIGINS=https://market.example.com \
  -e IDENTITY_SERVICE_URL=https://id.example.com \
  -e IDENTITY_ISSUER=https://id.example.com \
  -e IDENTITY_AUDIENCE=shellui \
  -e REDIS_URL=redis://your_redis_host_here:6379/0 \
  -e POSTGRES_DATABASE_URL= \
  shellui/marketplace-service:0.9.0
```

This Compose file starts Postgres and Redis in the same project:

```yaml
services:
  marketplace-service:
    image: shellui/marketplace-service:0.9.0
    ports:
      - "8000:8000"
    environment:
      SECRET_KEY: your_secret_key_here
      DEBUG: "false"
      ALLOWED_HOSTS: market.example.com
      CSRF_TRUSTED_ORIGINS: https://market.example.com
      IDENTITY_SERVICE_URL: https://id.example.com
      IDENTITY_ISSUER: https://id.example.com
      IDENTITY_AUDIENCE: shellui
      REDIS_URL: redis://redis:6379/0
      POSTGRES_DATABASE_URL: postgres://marketplace:marketplace@postgres:5432/marketplace
      POSTGRES_SSL_REQUIRE: "false"
      TRUST_PROXY: "true"
    depends_on:
      - postgres
      - redis
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: marketplace
      POSTGRES_PASSWORD: marketplace
      POSTGRES_DB: marketplace
  redis:
    image: redis:8-alpine
volumes: {}
```

The app redirects HTTP to HTTPS when `SECURE_SSL_REDIRECT` is true (the default when `DEBUG=false`). `GET /health/live` stays on HTTP and skips Django host checks. Set `ALLOWED_HOSTS` to `localhost` and `SECURE_SSL_REDIRECT=false` for an HTTP trial on your machine.

## Required environment variables

`manage.py check --deploy` requires these when `DEBUG=false`.

| Variable | Example | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | `your_secret_key_here` | Signs sessions, at least 50 characters |
| `DEBUG` | `false` | Production mode (the image default) |
| `ALLOWED_HOSTS` | `market.example.com` | Public host names, comma-separated |
| `CSRF_TRUSTED_ORIGINS` | `https://market.example.com` | Full HTTPS origin for Django admin |
| `REDIS_URL` | `redis://redis:6379/0` | Shared install rate limits |
| `IDENTITY_ISSUER` | `https://id.example.com` | JWT issuer |
| `IDENTITY_AUDIENCE` | `shellui` | JWT audience |
| `IDENTITY_JWKS` or `IDENTITY_SERVICE_URL` | a JWKS document or `https://id.example.com` | Token verification. A fetched URL must be https unless `DEBUG` is true |

Create the first admin user with `python manage.py createsuperuser` inside the container.
