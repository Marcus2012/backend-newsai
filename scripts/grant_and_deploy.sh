#!/usr/bin/env bash
set -euo pipefail

# Automate: create missing secrets, grant secretAccessor to Cloud Run service account, and trigger Cloud Build
# Usage: PROJECT_ID=asieselfutbol ./scripts/grant_and_deploy.sh

PROJECT_ID=${PROJECT_ID:-asieselfutbol}
SERVICE_NAME=${SERVICE_NAME:-newsai-backend}
REGION=${REGION:-us-east4}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME (region: $REGION)"

echo "1) Creating missing secrets from .env"
"$SCRIPT_DIR/create_secrets_if_missing.sh" || { echo "create_secrets_if_missing failed"; exit 1; }

echo "2) Obtain Cloud Run service account"
SERVICE_ACCOUNT=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(spec.template.spec.serviceAccountName)' --project="$PROJECT_ID" || true)
if [ -z "$SERVICE_ACCOUNT" ]; then
  PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
  SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi
echo "Service account: $SERVICE_ACCOUNT"

SECRETS_LIST=(STRAPI_URL STRAPI_TOKEN STRAPI_DEV_URL STRAPI_DEV_TOKEN GEMINI_API_KEY DATABASE_URL WP_AUTH_TOKEN FOOTYSTATS_API_KEY GROQ_API_KEY SECRET_KEY \
EASYPROMOS_API_TOKEN EASYPROMOS_CAMPAIGN_ID EASYPROMOS_API_AUTLOGIN EASYPROMOS_PROMO_BASE API_SPORTS_KEY API_SPORTS_BASE PERU_LEAGUE_ID PERU_SEASON)

echo "3) Grant secretmanager.secretAccessor to service account for each secret (will skip if secret missing)"
for name in "${SECRETS_LIST[@]}"; do
  if gcloud secrets describe "$name" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Granting access to $name"
    gcloud secrets add-iam-policy-binding "$name" \
      --member="serviceAccount:${SERVICE_ACCOUNT}" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID" || true
  else
    echo "Secret $name not found — skipping grant"
  fi
done

echo "4) Trigger Cloud Build (build + deploy)"
gcloud builds submit --config cloudbuild.yaml --project="$PROJECT_ID"

echo "Done. Monitor Cloud Run logs with: gcloud run logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
