# Create a global internal IP address for Private Service Connect
# Private Service Connect(PSC)를 위한 전역 내부 IP 주소를 생성합니다.
# 이 IP 주소는 Google API에 대한 비공개 연결 엔드포인트로 사용됩니다.
resource "google_compute_global_address" "default" {
  name         = "gemini-ip"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  network      = google_compute_network.default.id
  address_type = "INTERNAL"
  address      = "10.10.100.250"
}

# Create a global forwarding rule for Private Service Connect
# PSC를 위한 전역 전달 규칙을 생성합니다.
# 이 규칙은 위에서 생성한 내부 IP 주소로 들어오는 트래픽을
# 'all-apis' 번들(모든 Google API)로 전달합니다.
resource "google_compute_global_forwarding_rule" "default" {
  name                  = "pscgemini"
  target                = "all-apis"
  network               = google_compute_network.default.id
  ip_address            = google_compute_global_address.default.id
  load_balancing_scheme = ""
}