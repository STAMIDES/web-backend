#!/bin/sh
# Entrypoint script that ensures mandatory environment variables are set.

set -e

REQUIRED_VARS="POSTGRES_HOST POSTGRES_PORT POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB DOMINIO_FRONTEND"

for var in $REQUIRED_VARS; do
  if [ -z "$(eval echo \$$var)" ]; then
    echo "Error: environment variable $var is not set." >&2
    exit 1
  fi
done

# Allow conditional skip of migrations (useful for debug container)
if [ "$SKIP_MIGRATIONS" = "true" ] ; then
  echo "SKIP_MIGRATIONS=true – skipping database migrations."
else
  echo "Running database migrations..."
  python3 -m alembic upgrade head
fi

# All good – execute the container's main process.
exec "$@" 
