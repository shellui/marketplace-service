# Agent notes

## Shellui guidelines

When writing user-facing copy, follow the Shellui handbooks:

- Writing: https://shellui.com/guidelines/writing.md
- Building a page: https://shellui.com/design.md and https://shellui.com/guidelines/web-design.md

### Hard rules

- Product name is **Shellui**. This service is **Shellui Marketplace**. Do not call it an app store.
- Shellui Marketplace 0.9 is free. Do not add price, payment, checkout, or paid-listing fields.
- Ban em dashes and en dashes used as punctuation.
- Straight quotes. Ellipsis `…`, not three dots.

## This service

`marketplace-service` is the catalog behind [shellui/marketplace](https://github.com/shellui/marketplace) and `shellui add`.

- Public JSON is in `apps/catalog/serializers.py`. The directory reads `apps`, `app`, and `categories`. The CLI reads `name`, `url`, `path`, `official`, `safeForAuthToken`, and `icon` on the app object (or under `app`).
- Slugs may contain one slash. Routes accept `/api/apps/shellui/files` and `/api/apps/shellui%2Ffiles`.
- Identity Bearer tokens go through `shellui_django.mcp.identity_jwks.decode_identity_rs256_jwt`.
- Do not log or store raw IPs, origins, install ids, tokens, or user ids. See [SECURITY.md](SECURITY.md).
- `shellui-django` stays on 0.5.1, the same release as storage-service, email-service, and hosting-service.
- Dependabot targets `develop`, like those services. That branch does not exist yet.

## Checks

```bash
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```
