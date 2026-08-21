#!/bin/sh
set -e

echo "============================================================================="
echo ">>> Starting Promtail"
echo "============================================================================="

PROMTAIL_BIN="$(command -v promtail)"

echo ">>> Promtail binary: ${PROMTAIL_BIN}"

exec "${PROMTAIL_BIN}" \
  -config.file=/etc/promtail/promtail-config.yaml \
  -config.expand-env=true
