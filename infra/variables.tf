variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Deployment environment."
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.env)
    error_message = "env must be either 'staging' or 'production'."
  }
}

variable "image_tag" {
  description = "Container image tag for GHCR deployment."
  type        = string
}

variable "wallet_pem" {
  description = "Wallet PEM payload for secret manager."
  type        = string
  sensitive   = true
}

variable "config_secret_data" {
  description = "Configuration payload for secret manager volume mount."
  type        = string
  sensitive   = true
}
