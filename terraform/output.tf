# Output for the name of the VPC network
# 생성된 VPC 네트워크의 이름을 출력합니다.
output "network_name" {
  description = "The name of the VPC network."
  value       = google_compute_network.default.name
}

# Output for the name of the subnetwork
# 생성된 서브넷의 이름을 출력합니다.
output "subnetwork_name" {
  description = "The name of the subnetwork."
  value       = google_compute_subnetwork.default.name
}

# Output for the service account account id
output "service_account_account_id" {
  description = "The account id of the created service account."
  value       = google_service_account.sa.account_id
}