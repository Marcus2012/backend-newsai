#!/bin/bash

# Google Cloud Run Deployment Script
# This script automates the deployment of the News AI Generator backend to Google Cloud Run
# Prerequisites:
#   - gcloud CLI installed: https://cloud.google.com/sdk/docs/install
#   - Docker installed for local testing
#   - Authenticated: gcloud auth login
#   - Project set: gcloud config set project PROJECT_ID

set -e

# Configuration
SERVICE_NAME="${1:-newsai-backend}"
REGION="${2:-us-central1}"
PROJECT_ID="${3:-$(gcloud config get-value project)}"
IMAGE_URL="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Google Cloud Run Deployment${NC}"
echo "=================================="
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Project ID: $PROJECT_ID"
echo "Image URL: $IMAGE_URL"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}❌ Not authenticated. Run 'gcloud auth login' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}1️⃣  Building Docker image...${NC}"
docker build -t ${IMAGE_URL}:latest .
docker build -t ${IMAGE_URL}:$(date +%Y%m%d-%H%M%S) .

echo -e "${YELLOW}2️⃣  Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_URL}:latest

echo -e "${YELLOW}3️⃣  Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_URL}:latest \
    --region ${REGION} \
    --platform managed \
    --memory 1Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 100 \
    --min-instances 1 \
    --concurrency 80 \
    --allow-unauthenticated \
    --set-env-vars PYTHONUNBUFFERED=1 \
    --update-secrets DATABASE_URL=DATABASE_URL:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
GROQ_API_KEY=GROQ_API_KEY:latest,\
SECRET_KEY=SECRET_KEY:latest,\
WP_AUTH_TOKEN=WP_AUTH_TOKEN:latest,\
FOOTYSTATS_API_KEY=FOOTYSTATS_API_KEY:latest \
    --format json

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "To view logs:"
echo "  gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "To check the service:"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "To get the service URL:"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'"
