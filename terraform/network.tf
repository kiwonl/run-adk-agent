# 커스텀 모드 VPC 네트워크를 생성합니다. auto_create_subnetworks = false로 설정하여
# 서브넷을 수동으로 관리하고, 라우팅 모드를 GLOBAL로 설정하여 모든 리전의 리소스가 통신할 수 있도록 합니다.
resource "google_compute_network" "default" {
  project                 = var.project_id
  name                    = var.network_id
  auto_create_subnetworks = false
  mtu                     = 1460
  routing_mode            = "GLOBAL"
}

# 위에서 생성한 VPC 네트워크 내에 서브넷을 생성합니다.
resource "google_compute_subnetwork" "default" {
  name                     = var.subnet_name
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  stack_type               = "IPV4_ONLY"
  network                  = google_compute_network.default.id
  # private_ip_google_access = true
}

# 동적 라우팅 및 Cloud NAT의 제어부 역할을 하는 Cloud Router를 생성합니다.
# BGP(Border Gateway Protocol)를 사용하여 네트워크 정보를 교환합니다.
resource "google_compute_router" "default" {
  name    = "outbound-nat"
  region  = var.region
  network = google_compute_network.default.id

  bgp {
    asn = 64514
  }
}

# 외부 IP 주소가 없는 VM 인스턴스가 인터넷에 액세스할 수 있도록 Cloud NAT 게이트웨이를 생성합니다.
# 모든 서브넷의 모든 IP 범위를 NAT 대상으로 지정하고, 오류만 로깅하도록 설정합니다.
resource "google_compute_router_nat" "default" {
  name                               = "outbound-gw"
  router                             = google_compute_router.default.name
  region                             = google_compute_router.default.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}