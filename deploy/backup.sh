#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
key="db/$(date -u +%Y-%m-%dT%H%M%SZ).sql.gz"

docker compose -f compose.prod.yaml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip \
  | docker run --rm -i --env-file .env -e AWS_DEFAULT_REGION=eu-west-2 amazon/aws-cli \
      s3 cp - "s3://elisebeer-art-backups/$key"

echo "backed up to $key"
