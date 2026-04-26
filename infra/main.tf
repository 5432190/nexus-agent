terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "nexus-agent-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "run" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
}

resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
}

resource "google_service_account" "staging_agent" {
  account_id   = "nexus-agent-staging"
  project      = var.project_id
  display_name = "Nexus Agent Staging Runtime"
}

resource "google_service_account" "prod_agent" {
  account_id   = "nexus-agent-prod"
  project      = var.project_id
  display_name = "Nexus Agent Production Runtime"
}

locals {
  service_account_email = var.env == "production" ? google_service_account.prod_agent.email : google_service_account.staging_agent.email
}

resource "google_secret_manager_secret" "wallet_secret" {
  project    = var.project_id
  secret_id  = "wallet-pem"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "wallet_secret_version" {
  secret      = google_secret_manager_secret.wallet_secret.id
  secret_data = var.wallet_pem
}

resource "google_secret_manager_secret" "config_secret" {
  project    = var.project_id
  secret_id  = "nexus-config"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "config_secret_version" {
  secret      = google_secret_manager_secret.config_secret.id
  secret_data = var.config_secret_data
}

resource "google_cloud_run_v2_service" "agent" {
  name     = "nexus-agent-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    service_account = local.service_account_email

    containers {
      image = "ghcr.io/nexus-agent/nexus-agent:${var.image_tag}"

      env {
        name  = "ENV"
        value = var.env
      }

      secret_environment_variables {
        name       = "WALLET_SECRET"
        secret     = google_secret_manager_secret.wallet_secret.id
        version    = "latest"
      }

      secret_environment_variables {
        name       = "CONFIG_SECRET"
        secret     = google_secret_manager_secret.config_secret.id
        version    = "latest"
      }

      volume_mounts {
        name       = "wallet"
        mount_path = "/wallet"
        read_only  = true
      }

      volume_mounts {
        name       = "config"
        mount_path = "/config"
        read_only  = true
      }

      volume_mounts {
        name       = "audit"
        mount_path = "/audit"
        read_only  = false
      }
    }

    volumes {
      name = "wallet"
      secret {
        secret      = google_secret_manager_secret.wallet_secret.id
        secret_version = "latest"
      }
    }

    volumes {
      name = "config"
      secret {
        secret      = google_secret_manager_secret.config_secret.id
        secret_version = "latest"
      }
    }

    volumes {
      name = "audit"
      empty_dir {}
    }

    scaling {
      min_instance_count = var.env == "production" ? 1 : 0
    }
  }

  traffic {
    percent        = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "staging_invoker" {
  count = var.env == "staging" ? 1 : 0

  project = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.agent.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
