terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Cloud Storage Bucket for optional document archive
resource "google_storage_bucket" "nexusai_docs" {
  name          = "${var.project_id}-nexusai-documents"
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. Cloud SQL PostgreSQL 16 with pgvector extension enabled
resource "google_sql_database_instance" "nexusai_db_instance" {
  name             = "nexusai-postgres-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-custom-2-7680" # 2 vCPU, 7.5GB RAM
    
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }

    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "nexusai_database" {
  name     = "nexusai"
  instance = google_sql_database_instance.nexusai_db_instance.name
}

resource "google_sql_user" "nexusai_user" {
  name     = var.db_username
  instance = google_sql_database_instance.nexusai_db_instance.name
  password = var.db_password
}

# 3. Secret Manager for API Keys and Secrets
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gemini_api_key_version" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# 4. Cloud Run Services
resource "google_cloud_run_v2_service" "backend" {
  name     = "nexusai-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = "gcr.io/${var.project_id}/nexusai-backend:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql+psycopg://${var.db_username}:${var.db_password}@/${google_sql_database.nexusai_database.name}?host=/cloudsql/${google_sql_database_instance.nexusai_db_instance.connection_name}"
      }
    }
  }
}
