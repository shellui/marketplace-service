# Configuration

Settings are environment variables. `python manage.py generate_env --host market.example.com` prints a production set.

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | required | 50+ characters when `DEBUG=false` |
| `DEBUG` | `false` | `true` allows `http://localhost` URLs and skips the Redis deploy check |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `CSRF_TRUSTED_ORIGINS` | local origins | Full origins for Django admin |
| `POSTGRES_DATABASE_URL` | empty | Empty uses SQLite (`SQLITE_PATH`) |
| `POSTGRES_SSL_REQUIRE` | `true` when `DEBUG=false` | Set `false` for the local Postgres container |
| `REDIS_URL` | empty | Required when `DEBUG=false` |
| `STORAGE_BACKEND` | `filesystem` | `s3` stores uploaded icons and screenshots |
| `AWS_STORAGE_BUCKET_NAME` | empty | Required for `s3` |
| `AWS_S3_ENDPOINT_URL` | empty | MinIO, R2, or another S3-compatible endpoint |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | empty | S3 credentials |
| `IDENTITY_SERVICE_URL` | empty | Used to build the JWKS URL when no pin is set |
| `IDENTITY_JWKS_URL` | derived | Fetched JWKS. https unless `DEBUG` is true. Redirects are not followed. |
| `IDENTITY_JWKS` | empty | Inline JWKS JSON. Preferred in production |
| `IDENTITY_JWKS_FILE` | empty | Path to a JWKS file |
| `IDENTITY_ISSUER` | empty | Required when `DEBUG=false` |
| `IDENTITY_AUDIENCE` | empty | Required when `DEBUG=false` |
| `CORS_ALLOW_ALL_ORIGINS` | `true` | Catalog `GET` and install `POST` send `Access-Control-Allow-Origin: *` |
| `TRUST_PROXY` | `true` when `DEBUG=false` | Use the first `X-Forwarded-For` hop for the rate-limit hash |
| `CATALOG_CACHE_SECONDS` | `60` | `0` disables catalog caching |
| `INSTALL_RATE` | `30/min` | Per hashed client address |
| `TRENDING_WINDOW_DAYS` | `7` | Window for `trending` |
| `SECURE_SSL_REDIRECT` | `true` when `DEBUG=false` | `/health/live` is answered before the redirect |
| `SENTRY_DSN` | empty | Errors only. `send_default_pii` is false |

`check --deploy` reports `marketplace.E001` through `marketplace.E005` when production settings are missing. The Docker entrypoint runs that check.

Coolify can set the same variables on the container. Map port 8000, mount `/app/data` when using SQLite or filesystem media, and set `TRUST_PROXY=true` behind the proxy.
