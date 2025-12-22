# Terraform block to define required providers
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Provider block to configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}