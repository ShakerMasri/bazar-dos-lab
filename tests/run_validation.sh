#!/usr/bin/env bash
# Runs the COMPLETE validation against disposable Compose containers and volumes.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

export BAZAR_TEST_PROJECT="shaker_bazar_validation"
export FRONTEND_HOST_PORT=5100
export CATALOG_HOST_PORT=5101
export BAZAR_TEST_FRONTEND="http://127.0.0.1:${FRONTEND_HOST_PORT}"
export BAZAR_TEST_CATALOG="http://127.0.0.1:${CATALOG_HOST_PORT}"

command -v docker >/dev/null || { echo 'Docker required'; exit 1; }
python3 -c 'import requests' || { echo 'Install requests: python3 -m pip install -r requirements-dev.txt'; exit 1; }

# Refuse to overwrite an existing testing stack accidentally.
if [[ -n "$(docker compose -p "$BAZAR_TEST_PROJECT" ps -aq)" ]]; then
  echo "Test project already exists: $BAZAR_TEST_PROJECT"
  echo "Inspect it before deleting anything; refusing to overwrite test volumes."
  exit 1
fi

cleanup() {
  echo "Saving isolated service logs in docs/service-logs.txt..."
  docker compose -p "$BAZAR_TEST_PROJECT" logs --no-color catalog order frontend > docs/service-logs.txt 2>&1 || true
  echo "Deleting ONLY the isolated '$BAZAR_TEST_PROJECT' containers and volumes..."
  docker compose -p "$BAZAR_TEST_PROJECT" down -v --remove-orphans || true
}
trap cleanup EXIT

mkdir -p docs
docker compose -p "$BAZAR_TEST_PROJECT" up -d --build

# stdout and stderr are recorded; failure remains visible (pipefail).
python3 -u tests/e2e_validation.py 2>&1 | tee docs/sample-output.txt
