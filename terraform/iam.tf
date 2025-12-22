# Cloud Run 을 위한 Service Account
resource "google_service_account" "sa" {
  project      = var.project_id
  account_id   = var.run_service_account
  display_name = "google_service_account"
}

# Cloud Run SA에 권한 추가 - AIplatform AI
resource "google_project_iam_member" "ai_platform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.sa.email}"
}

# Cloud Run SA에 권한 추가 - Run Invoker
resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.sa.email}"
}