# API

OpenAPI: `/api/schema/`, Swagger UI: `/api/docs/`, ReDoc: `/api/docs/redoc/`.

## `GET /api/apps`

Query parameters:

| Name | Values |
| --- | --- |
| `q` | Search name, tagline, description, slug, publisher, tags |
| `category` | Category id, such as `productivity` |
| `official` | `true` or `false` |
| `sort` | `popular` (default), `recent`, `name` |
| `page` | Page number, starting at 1 |
| `page_size` | 1 to 100, default 24 |

```json
{
  "apps": [],
  "count": 0,
  "page": 1,
  "pageSize": 24,
  "next": null,
  "previous": null
}
```

Only published apps are included. `installCount` is the curated baseline plus active installs. `trending` is true for up to three apps with the most install events in the last 7 days.

The app object matches the directory client: `slug`, `name`, `tagline`, `description`, `publisher` (`name`, `kind`, `url`), `category`, `version`, `homepage`, `support`, `icon`, `screenshots`, `installCount`, `updatedAt`, `featured`, `capabilities`, `navigation`.

It also includes the fields `shellui add` reads on the same object: `name`, `url` (the navigation URL), `path`, `official`, `safeForAuthToken`, `icon`, `capabilities`.

`publisher.kind` is `official`, `verified`, or `community`.

## `GET /api/apps/<slug>`

```json
{ "app": { "slug": "files" } }
```

`<slug>` may contain one slash. `GET /api/apps/shellui/files` and `GET /api/apps/shellui%2Ffiles` are the same app.

## `GET /api/categories`

```json
{ "categories": [{ "id": "productivity", "label": "Productivity" }] }
```

## `POST /api/apps/<slug>/install` and `uninstall`

`Content-Type: application/json`. CSRF is not required. CORS allows `*`.

Anonymous, counted:

```json
{ "installId": "browser-install-id" }
```

Send `Origin: https://your-shell.example`. Optional header `X-Shellui-Install-Id` is the same id.

Signed in: `Authorization: Bearer <Identity access token>`. The token is an RS256 JWT with `iss`, `aud`, `sub`, `exp`, `iat`, `scope`, and `jti`, verified against the configured Identity JWKS.

```json
{ "ok": true, "counted": true, "active": true, "installCount": 1841 }
```

Missing dedupe key:

```json
{ "ok": true, "counted": false, "active": false, "installCount": 1840, "reason": "dedupe_key_required" }
```

Errors use `{ "detail": "..." }` with status 400, 401, 404, 415, or 429.

## Capabilities

`theme`, `locale`, `ui`, `navigate`, `storage`, `ai`. `auth` is stored only on official apps. Third-party apps that ask for it fail validation.
