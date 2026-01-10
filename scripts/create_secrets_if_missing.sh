#!/usr/bin/env bash
set -euo pipefail

# Usage: PROJECT_ID=your-project ./scripts/create_secrets_if_missing.sh
PROJECT_ID=${PROJECT_ID:-asieselfutbol}
ENV_FILE="${ENV_FILE:-.env}"

# Secrets to create (will skip if not present in .env)
SECRETS="STRAPI_URL STRAPI_TOKEN STRAPI_DEV_URL STRAPI_DEV_TOKEN GEMINI_API_KEY DATABASE_URL WP_AUTH_TOKEN FOOTYSTATS_API_KEY GROQ_API_KEY SECRET_KEY \
EASYPROMOS_API_TOKEN EASYPROMOS_CAMPAIGN_ID EASYPROMOS_API_AUTLOGIN EASYPROMOS_PROMO_BASE API_SPORTS_KEY API_SPORTS_BASE PERU_LEAGUE_ID PERU_SEASON"

get_env() {
  key="$1"
  if [ ! -f "$ENV_FILE" ]; then
    echo ""
    return
  fi
  val=$(grep -m1 -E "^${key}=" "$ENV_FILE" || true)
  if [ -z "$val" ]; then
    echo ""
    return
  fi
  val=${val#${key}=}
  # strip surrounding quotes (handle both "..." and '...')
  # remove surrounding double-quotes
  if [ "${#val}" -ge 2 ] && [ "${val:0:1}" = '"' ] && [ "${val: -1}" = '"' ]; then
    val="${val:1:${#val}-2}"
  fi
  # remove surrounding single-quotes
  if [ "${#val}" -ge 2 ] && [ "${val:0:1}" = "'" ] && [ "${val: -1}" = "'" ]; then
    val="${val:1:${#val}-2}"
  fi
  printf '%s' "$val"
}

for name in $SECRETS; do
  value=$(get_env "$name")
  if [ -z "$value" ]; then
    echo "[SKIP] $name not found in $ENV_FILE"
    continue
  fi

  if gcloud secrets describe "$name" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "[EXISTS] $name already exists — skipping"
  else
    echo "[CREATE] Creating secret: $name"
    printf '%s' "$value" | gcloud secrets create "$name" --data-file=- --replication-policy="automatic" --project="$PROJECT_ID"
  fi
done

echo "Done. Review created secrets with: gcloud secrets list --project=$PROJECT_ID"
