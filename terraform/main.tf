data "google_project" "project" {
}

# Enable necessary Google Cloud APIs for the project
resource "google_project_service" "default" {
  project = var.project_id
  
  for_each = toset([
    "cloudbuild.googleapis.com",          # Cloud Build API
    "artifactregistry.googleapis.com",    # Artifact Registry API
    "dns.googleapis.com",                 # Google Cloud DNS API
    "aiplatform.googleapis.com",          # Vertex AI API
    "servicedirectory.googleapis.com",    # Service Directory API
    "run.googleapis.com",                 # Cloud Run API
    "cloudresourcemanager.googleapis.com" # Cloud Resource Manager API
  ])

  service            = each.value
  disable_on_destroy = false
}