# Getting started

## Docker

```bash
cp .env.example .env
# set SECRET_KEY
docker compose up --build
```

Open [http://localhost:8010](http://localhost:8010). The catalog is at `/api/apps`. Admin is at `/admin/`.

```bash
docker compose exec marketplace-service python manage.py createsuperuser
```

Compose starts Postgres 16 and Redis 8. Icons uploaded in admin are stored on the `marketplace-service-data` volume unless `STORAGE_BACKEND=s3`.

## Without Docker

```bash
uv sync --group dev
export SECRET_KEY=dev-only-secret-key-change-me-0123456789abcd
export DEBUG=true
uv run python manage.py migrate
uv run python manage.py seed_marketplace
uv run python manage.py runserver 8010
```

`migrate` runs the data migration that loads the same seed.

## Directory and CLI

Point the directory at this origin with `VITE_MARKETPLACE_API_URL`. Point the CLI at it with `shellui add <app-id> --api-url http://localhost:8010`.

To count an install, the shell sends a Bearer token from identity-service, or the directory sends:

```json
{ "installId": "a-stable-anonymous-id" }
```

The browser `Origin` header is required for anonymous counts. The current directory sends `{}` and the ping is accepted without moving the count.
