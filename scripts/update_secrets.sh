#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found. Run this from repo root where .env exists."
  exit 1
fi

# Helper to extract value (strips surrounding quotes)
get() {
  grep -E "^$1=" "$ENV_FILE" | sed -E "s/^$1=//" | sed -E 's/^"(.*)"$/\1/' | sed -E "s/^'(.*)'$/\1/"
}

declare -a secrets=(
  "STRAPI_URL"
  "STRAPI_TOKEN"
  "STRAPI_DEV_URL"
  "STRAPI_DEV_TOKEN"
  "GEMINI_API_KEY"
  "DATABASE_URL"
  "WP_AUTH_TOKEN"
  "GROQ_API_KEY"
  "SECRET_KEY"
  "EASYPROMOS_API_TOKEN"
  "EASYPROMOS_CAMPAIGN_ID"
  "EASYPROMOS_API_AUTLOGIN"
  "EASYPROMOS_PROMO_BASE"
  "SPORTMONKS_API_TOKEN"
  "SCRAPE_URLS"
)

for s in "${secrets[@]}"; do
  val=$(get "$s" || true)
  if [ -z "$val" ]; then
    echo "Warning: $s is empty or missing in $ENV_FILE — skipping"
    continue
  fi

  if ! gcloud secrets describe "$s" >/dev/null 2>&1; then
    echo "Creating secret: $s"
    gcloud secrets create "$s" --replication-policy="automatic"
  else
    echo "Secret exists: $s — adding new version"
  fi

  # Add new secret version from stdin
  echo -n "$val" | gcloud secrets versions add "$s" --data-file=- >/dev/null
  echo "Updated secret $s"
done

echo "All done. Verify with: gcloud secrets versions access latest --secret=DATABASE_URL"