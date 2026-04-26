output "service_url" {
  description = "Cloud Run service URL."
  value       = google_cloud_run_v2_service.agent.uri
}

output "service_identity_email" {
  description = "Email of the Cloud Run runtime service account."
  value       = local.service_account_email
}

output "secret_version_name" {
  description = "Secret Manager wallet secret version name."
  value       = google_secret_manager_secret_version.wallet_secret_version.name
}
