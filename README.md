# marketplace-service

Catalog and install stats for Shellui Marketplace.

[![CI](https://github.com/shellui/marketplace-service/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/shellui/marketplace-service/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Shellui Marketplace is the public directory of apps for the shell. This service stores the catalog, serves it to the [directory](https://github.com/shellui/marketplace) and to `shellui add`, and counts installs. Every listing in 0.9 is free. There is no pricing, payment, or checkout.

## Get started

You need Docker and Git.

```bash
git clone https://github.com/shellui/marketplace-service.git
cd marketplace-service
cp .env.example .env   # then set SECRET_KEY
docker compose up --build
```

The API runs on [http://localhost:8010](http://localhost:8010). `/api/docs/` is the OpenAPI reference and `/admin/` is Django admin. Create an admin user with `docker compose exec marketplace-service python manage.py createsuperuser`.

The directory reads:

```text
VITE_MARKETPLACE_API_URL=http://localhost:8010
```

`shellui add <app-id>` reads `GET /api/apps/<app-id>`.

## Configuration

For production, `python manage.py generate_env --host market.example.com` prints the required settings with a fresh `SECRET_KEY`.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret, 50+ characters when `DEBUG=false` |
| `POSTGRES_DATABASE_URL` | Postgres URL. Empty uses SQLite on the volume |
| `REDIS_URL` | Required when `DEBUG=false`. Shared install rate limits |
| `IDENTITY_ISSUER`, `IDENTITY_AUDIENCE` | Must match identity `JWT_ISSUER` and `JWT_AUDIENCE` |
| `IDENTITY_JWKS` or `IDENTITY_JWKS_URL` | Keys that verify optional install Bearer tokens |
| `STORAGE_BACKEND` | `filesystem` (default) or `s3` for icons and screenshots |

Every setting is in [Configuration](docs/configuration.md).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/apps` | Published apps. Query: `q`, `category`, `official`, `sort` (`popular`, `recent`, `name`), `page`, `page_size` |
| `GET` | `/api/apps/<slug>` | One published app. Slugs may contain one slash (`shellui/files`) |
| `GET` | `/api/categories` | Categories that have a published app |
| `POST` | `/api/apps/<slug>/install` | Record an install |
| `POST` | `/api/apps/<slug>/uninstall` | Record an uninstall |

`GET` responses are JSON, cacheable, and send `Access-Control-Allow-Origin: *`. Install posts are CSRF-exempt JSON. A signed-in shell sends `Authorization: Bearer <Identity JWT>`. An anonymous client sends `{"installId":"<8-128 chars>"}` and an `Origin` header. Those values are hashed and not stored. A post without either key returns `counted: false`, which is what the directory does today. See [API](docs/api.md).

`GET /health/live` is the process probe. `GET /health/ready` checks the database. `GET /metrics` is Prometheus text.

## Documentation

The handbook lives in [`docs/`](docs/index.md). The central site will publish it at [docs.shellui.com/marketplace](https://docs.shellui.com/marketplace) when the docs build includes this service.

- [Getting started](docs/getting-started.md)
- [API](docs/api.md)
- [Configuration](docs/configuration.md)
- [Threat model](SECURITY.md)

## Run locally

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_marketplace
uv run python manage.py runserver 8010
uv run python manage.py test
```

`seed_marketplace` loads the same official apps as the directory fallback (Files, Admin, Dashboard, AI Assistant, Docs) and the sample community listings (Notes, Status Board). A data migration loads that seed on `migrate` as well.

## Development

Releases go to Docker Hub as `shellui/marketplace-service`. The image page is created on the first publish. The checklist is in [PUBLISH.md](PUBLISH.md) and the overview text is in [DOCKERHUB.md](DOCKERHUB.md). Changes are in [CHANGELOG.md](CHANGELOG.md).

Dependabot is configured like the other Shellui services, with `target-branch: develop`. This repository does not have a `develop` branch yet. Create it before expecting Dependabot pull requests. Day-to-day work for 0.9 is on `main`.

CI runs the tests, Ruff, a dependency audit, a secret scan, a link check, and a Docker build. Coding agents start with [AGENTS.md](AGENTS.md).

## Shellui projects

| Project | What it does |
| --- | --- |
| [shellui](https://github.com/shellui/shellui) | The shell, CLI and SDK |
| [marketplace](https://github.com/shellui/marketplace) | Shellui Marketplace directory |
| [admin](https://github.com/shellui/admin) | Administration app inside the shell |
| [files](https://github.com/shellui/files) | File explorer for storage-service |
| [identity-service](https://github.com/shellui/identity-service) | Sign-in, companies and tokens |
| [storage-service](https://github.com/shellui/storage-service) | File storage |
| [hosting-service](https://github.com/shellui/hosting-service) | Deploys and serves Shellui apps |
| [email-service](https://github.com/shellui/email-service) | Templates and sends email |

## License

[MIT](LICENSE)
