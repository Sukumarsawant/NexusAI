#!/usr/bin/env bash
set -euo pipefail

# NexusAI - Google Cloud Platform Deployment Script
# Prerequisites: gcloud CLI, docker, terraform

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy-gcp.sh <PROJECT_ID> [REGION]"
    exit 1
fi

echo "=========================================================="
echo "Deploying NexusAI to Google Cloud Platform"
echo "Project: $PROJECT_ID | Region: $REGION"
echo "=========================================================="

# 1. Enable required Google Cloud APIs
echo "[1/5] Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    containerregistry.googleapis.com \
    storage.googleapis.com \
    --project="$PROJECT_ID"

# 2. Build and push Docker images
echo "[2/5] Building and pushing container images..."
gcloud auth configure-docker --quiet

docker build -t "gcr.io/$PROJECT_ID/nexusai-backend:latest" -f backend/Dockerfile backend/
docker push "gcr.io/$PROJECT_ID/nexusai-backend:latest"

docker build -t "gcr.io/$PROJECT_ID/nexusai-frontend:latest" -f frontend/Dockerfile frontend/
docker push "gcr.io/$PROJECT_ID/nexusai-frontend:latest"

# 3. Provision Cloud SQL (PostgreSQL with pgvector) and Secrets
echo "[3/5] Deploying Cloud Run Backend..."
sed "s/PROJECT_ID/$PROJECT_ID/g; s/REGION/$REGION/g" infrastructure/gcp/cloud-run-backend.yaml | gcloud run services replace - --region="$REGION" --project="$PROJECT_ID"

echo "[4/5] Deploying Cloud Run Frontend..."
sed "s/PROJECT_ID/$PROJECT_ID/g; s/REGION/$REGION/g" infrastructure/gcp/cloud-run-frontend.yaml | gcloud run services replace - --region="$REGION" --project="$PROJECT_ID"

# 5. Allow unauthenticated ingress for public access
echo "[5/5] Granting public access..."
gcloud run services add-iam-policy-binding nexusai-frontend \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region="$REGION" \
    --project="$PROJECT_ID"

echo "=========================================================="
echo "NexusAI deployed successfully to Google Cloud Run!"
gcloud run services describe nexusai-frontend --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)"
echo "=========================================================="
