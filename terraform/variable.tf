# Variable for the Google Cloud project ID
variable "project_id" {
  type        = string
  description = "The ID of the Google Cloud project."
  default     = "your-gcp-project-id"
}

# Variable for the Google Cloud region
variable "region" {
  description = "The region for the resources."
  type        = string
  default     = "us-central1"
}

# Variable for the VPC network ID
variable "network_id" {
  type        = string
  description = "The ID of the VPC network."
  default     = "run-ai-apps-network"
}

# Variable for the subnetwork name
variable "subnet_name" {
  type        = string
  description = "The name of the subnetwork."
  default     = "run-ai-apps-subnet"
}

# Variable for the subnetwork CIDR
variable "subnet_cidr" {
  type        = string
  description = "The CIDR block for the subnetwork."
  default     = "192.168.100.0/24"
}

# Variable for the service account
variable "run_service_account" {
  type        = string
  description = "The ID of the service account."
  default     = "run-ai-apps-sa"
}