#!/usr/bin/env bash
# Container entrypoint.
#
# Modes (first argument, default "web"):
#   web    migrate, check --deploy, then gunicorn
#   other  run the given command as appuser, for example: python manage.py shell
#
# Production (DEBUG false, the image default) requires REDIS_URL. Redis is the
# shared cache behind install rate limits. The same rule is marketplace.E002.
set -euo pipefail

MODE="${1:-web}"
if [ "$#" -gt 0 ]; then
  shift
fi

APP_USER="${APP_USER:-appuser}"

log() {
  echo "entrypoint: $*" >&2
}

AS_APP=(
  setpriv --reuid="${APP_USER}" --regid="${APP_USER}" --init-groups --
  env HOME="/home/${APP_USER}" USER="${APP_USER}"
)

is_true() {
  case "$(printf '%s' "${1:-}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')" in
    1 | true | yes | on) return 0 ;;
    *) return 1 ;;
  esac
}

is_set() {
  [ -n "$(printf '%s' "${1:-}" | tr -d '[:space:]')" ]
}

require_redis_in_production() {
  if is_true "${DEBUG:-false}" || is_set "${REDIS_URL:-}"; then
    return 0
  fi
  log "ERROR: REDIS_URL is required when DEBUG is false (example: redis://redis:6379/0)."
  log "ERROR: Redis backs the shared install rate-limit cache."
  log "ERROR: Add a Redis service and set REDIS_URL, or set DEBUG=true for local development only."
  exit 1
}

prepare_data_dir() {
  local sqlite_file sqlite_dir media_dir
  sqlite_file="${SQLITE_PATH:-/app/data/db.sqlite3}"
  sqlite_dir="$(dirname "${sqlite_file}")"
  media_dir="${MEDIA_ROOT:-/app/data/media}"
  mkdir -p "${sqlite_dir}" "${media_dir}"
  chown -R "${APP_USER}:${APP_USER}" "${sqlite_dir}" "${media_dir}"
}

gunicorn_cmd() {
  GUNICORN_ARGS=(
    gunicorn
    --bind 0.0.0.0:8000
    --worker-class gthread
    --workers "${GUNICORN_WORKERS:-2}"
    --threads "${GUNICORN_THREADS:-2}"
    --timeout "${GUNICORN_TIMEOUT:-60}"
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}"
    --keep-alive "${GUNICORN_KEEP_ALIVE:-75}"
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}"
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-200}"
    --worker-tmp-dir /dev/shm
    --access-logfile -
    --logger-class config.safe_access_log.SafeAccessLogger
    --error-logfile -
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s "-" "%(a)s" %(M)sms req=%({x-request-id}o)s'
    config.wsgi:application
  )
}

case "${MODE}" in
  web)
    require_redis_in_production
    prepare_data_dir
    "${AS_APP[@]}" python manage.py migrate --noinput
    "${AS_APP[@]}" python manage.py seed_marketplace
    "${AS_APP[@]}" python manage.py check --deploy
    gunicorn_cmd
    exec "${AS_APP[@]}" "${GUNICORN_ARGS[@]}"
    ;;
  *)
    prepare_data_dir
    exec "${AS_APP[@]}" "${MODE}" "$@"
    ;;
esac
