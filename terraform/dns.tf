# DNS Managed Zone for private access to Google APIs
# googleapis.com. 도메인에 대한 비공개 DNS 영역을 생성합니다.
# 이 영역은 VPC 네트워크 내에서만 확인 가능하며, Google API에 대한 비공개 액세스를 가능하게 합니다.
resource "google_dns_managed_zone" "private_zone" {
  name       = "googleapis-private"
  dns_name   = "googleapis.com."
  visibility = "private"
  project    = var.project_id

  private_visibility_config {
    networks {
      network_url = google_compute_network.default.id
    }
  }
}

# "googleapis.com"에 대한 A 레코드를 생성하여 PSC 엔드포인트의 IP 주소로 확인되도록 합니다.
resource "google_dns_record_set" "a_record" {
  name         = "googleapis.com."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.private_zone.name
  project      = var.project_id

  rrdatas = [google_compute_global_address.default.address]
}

# "*.googleapis.com"에 대한 CNAME 레코드를 생성하여 모든 하위 도메인이 "googleapis.com"으로 확인되도록 합니다.
resource "google_dns_record_set" "cname_record" {
  name         = "*.googleapis.com."
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.private_zone.name
  project      = var.project_id

  rrdatas = ["googleapis.com."]
}