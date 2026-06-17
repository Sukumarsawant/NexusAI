variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment Environment (staging/production)"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "Cloud SQL database user"
  type        = string
  default     = "nexus_admin"
}

variable "db_password" {
  description = "Cloud SQL database password"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}
