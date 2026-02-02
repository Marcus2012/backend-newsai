#!/usr/bin/env bash
set -euo pipefail

# Switch Google Cloud credentials/config for a single project on the same dev machine.
# Usage:
#   ./scripts/switch_gcloud_project.sh
#
# Optional env vars:
#   PROJECT_ID=asieselfutbol
#   CONFIG_NAME=asieselfutbol
#   ACCOUNT=user@example.com
#   RUN_LOGIN=1
#   RUN_ADC_LOGIN=1

PROJECT_ID=${PROJECT_ID:-asieselfutbol}
CONFIG_NAME=${CONFIG_NAME:-${PROJECT_ID}}
ACCOUNT=${ACCOUNT:-datadriven111@gmail.com}

RUN_LOGIN=${RUN_LOGIN:-1}
RUN_ADC_LOGIN=${RUN_ADC_LOGIN:-1}

ensure_config() {
  local cfg="$1"
  if ! gcloud config configurations list --format="value(name)" | grep -qx "$cfg"; then
    gcloud config configurations create "$cfg" >/dev/null
  fi
}

ensure_config "$CONFIG_NAME"
gcloud config configurations activate "$CONFIG_NAME" >/dev/null
gcloud config set project "$PROJECT_ID" >/dev/null

if [ -n "$ACCOUNT" ]; then
  gcloud config set account "$ACCOUNT" >/dev/null
fi

if [ "$RUN_LOGIN" = "1" ]; then
  gcloud auth login --brief
fi

if [ "$RUN_ADC_LOGIN" = "1" ]; then
  gcloud auth application-default login
fi

echo "Activo: $(gcloud config configurations describe "$CONFIG_NAME" --format='value(name)')"
echo "Proyecto: $(gcloud config get-value project)"
echo "Cuenta: $(gcloud config get-value account)"
echo ""
echo "Exporta en tu shell si lo necesitas:"
echo "  export PROJECT_ID=\"$PROJECT_ID\""
echo "  export GOOGLE_CLOUD_PROJECT=\"$PROJECT_ID\""
echo ""
echo "Iniciando Cloud SQL Proxy..."
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud_sql_proxy" \
  -dir=/tmp \
  -instances="${PROJECT_ID}:us-east4:newsai"