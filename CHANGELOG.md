# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.9.0] - 2026-11-20

### ✨ Feature

- Initial Shellui Marketplace service: categories, apps, versions, screenshots, active installs, and an install event log.
- Public catalog: `GET /api/apps`, `GET /api/apps/<slug>`, `GET /api/categories`, with search, filters, sort, and pagination.
- Install stats: `POST /api/apps/<slug>/install` and `POST /api/apps/<slug>/uninstall`. Optional Identity Bearer tokens are verified with `shellui-django`. Anonymous posts are deduped by a hash of origin and install id.
- Django admin for curation, ordered icon and screenshot uploads, and an install analytics view.
- `seed_marketplace` and a data migration load the directory fallback catalog.
- OpenAPI at `/api/schema/`, Prometheus at `/metrics`, probes at `/health/live` and `/health/ready`.

### 🔒 Security

- Threat model in [SECURITY.md](SECURITY.md): catalog poisoning, navigation templates, stats spam, and PII.
- `auth` and `safeForAuthToken` are rejected for third-party apps.
- Public URLs must be https. `http://localhost` is accepted only when `DEBUG` is true.
- Install posts do not store raw IP addresses, origins, install ids, or user ids.
