# Deployment Guide: Local & Google Cloud Platform

This document describes how to deploy NexusAI locally via Docker Compose and to Google Cloud Platform using Cloud Run, Cloud SQL, and Google Cloud Storage.

---

## 1. Local Deployment (Docker Compose)

### Prerequisites
- Docker (version 24+)
- Docker Compose (version 2.20+)

### Quick Start
```bash
# 1. Clone repository and navigate to root
cd nexusai

# 2. Configure environment
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY

# 3. Build and launch all services
docker compose up --build
```

### Endpoints
- **Frontend Dashboard**: http://localhost:80 or http://localhost:5173
- **Backend API Docs (Swagger UI)**: http://localhost:8000/docs
- **Health Probes**: http://localhost:8000/health and http://localhost:8000/ready
- **PostgreSQL + pgvector**: localhost:5432

---

## 2. Google Cloud Platform (GCP) Deployment

### Architecture on GCP
- **Compute**: Google Cloud Run (Serverless, autoscaling 1-10 instances)
- **Database**: Cloud SQL for PostgreSQL 16 with `cloudsql.enable_pgvector=on`
- **Secrets**: Google Secret Manager (`gemini-api-key`, `nexusai-db-url`, `jwt-secret`)
- **Document Storage**: Google Cloud Storage (GCS) Bucket

### Required IAM Permissions
The deployment identity requires:
- `roles/run.admin`
- `roles/cloudsql.admin`
- `roles/secretmanager.admin`
- `roles/storage.admin`
- `roles/artifactregistry.writer`

### Automated Deployment Script
```bash
chmod +x infrastructure/gcp/deploy-gcp.sh
./infrastructure/gcp/deploy-gcp.sh <YOUR_GCP_PROJECT_ID> us-central1
```

### Terraform Infrastructure as Code
To provision Cloud SQL with pgvector, Cloud Run, and GCS using Terraform:
```bash
cd infrastructure/gcp/terraform
terraform init
terraform plan -var="project_id=<PROJECT_ID>" -var="gemini_api_key=<API_KEY>" -var="db_password=<STRONG_PASS>"
terraform apply -auto-approve
```
