# Publish marketplace-service

1. Update `version` in `pyproject.toml` and add a section to `CHANGELOG.md`.
2. Run the checks in [AGENTS.md](AGENTS.md). `uv lock` if dependencies changed.
3. Tag the release: `git tag vX.Y.Z` and push the tag.
4. Build and push `shellui/marketplace-service:X.Y.Z` and `:latest` from this Dockerfile. The Docker Hub overview is [DOCKERHUB.md](DOCKERHUB.md).
5. Confirm `/health/live` returns `ok` and `/api/apps` lists the seed catalog.

Do not put secrets in the image. Production sets `SECRET_KEY`, `REDIS_URL`, Postgres, and the Identity JWKS at runtime.
