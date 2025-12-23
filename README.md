# Google Cloud Run을 활용한 AI Agent 인프라

## 🌟 개요

이 프로젝트는 Google Cloud Platform(GCP)에서 정교한 멀티 에이전트 AI 시스템을 배포하기 위한 포괄적인 구성을 제공합니다. 방문객에게 동물 정보 제공 및 쇼 예약 서비스를 지원하는 **동물원 컨시어지 시스템(Zoo Concierge System)**이라는 실제 사용 사례를 통해 이를 시연합니다.

이 아키텍처는 최신 기술을 활용하여 확장 가능하고 안전한 에이전트 생태계를 구축합니다.

*   **zoo_concierge_agent**: 사용자의 주요 진입점입니다. "연구원(Researcher)" 하위 에이전트(동물원 데이터를 위한 MCP 서버 및 일반 사실 정보를 위한 Google 검색과 연결됨)를 사용하여 일반적인 문의를 처리하고, 예약 요청은 전문 에이전트로 라우팅합니다.
*   **zoo_show_agent**: 쇼 일정 및 예약 관리를 전담하는 전문 에이전트입니다. **A2A(Agent-to-Agent)** 프로토콜을 통해 메인 에이전트와 통신합니다.
*   **MCP 서버**: 두 개의 커스텀 **Model Context Protocol (MCP)** 서버(`zoo_animal_mcp_server` 및 `zoo_show_mcp_server`)는 에이전트 로직과 분리된 고유 동물원 데이터에 대한 구조화된 액세스를 제공합니다.

전체 인프라는 **Terraform**을 사용하여 프로비저닝되어, VPC, 비공개 네트워킹 및 IAM 정책을 포함한 안전하고 프로덕션 환경에 적합한 환경을 보장하며, 모든 구성 요소는 **Google Cloud Run**에 배포됩니다.

![ai-agent-design](./images/ai-agent-design.png)

## 🚀 주요 기술

*   **Google Cloud Run**: 확장성이 뛰어난 컨테이너화된 애플리케이션을 배포하기 위한 완전 관리형 서버리스 플랫폼입니다.
*   **Model Context Protocol (MCP)**: AI 모델이 외부 데이터 소스 및 도구에 안전하게 연결할 수 있도록 하는 개방형 표준입니다.
*   **Google ADK (Agent Development Kit)**: GenAI 에이전트를 구축, 테스트 및 배포하기 위한 Python 프레임워크입니다.
*   **A2A (Agent-to-Agent) Protocol**: 독립적인 에이전트들이 서로를 검색하고 상호 작용하여 복잡한 작업을 협업하여 해결할 수 있도록 하는 메커니즘입니다.
*   **Terraform**: 클라우드 리소스를 일관되게 정의하고 프로비저닝하기 위한 코드형 인프라(IaC) 도구입니다.

---

## 🛠️ 시작하기

### Terraform을 통한 인프라 설정

1.  **환경 변수 설정:**
    `run-adk-agent` 디렉토리의 루트에서 시작합니다.
    
    ```bash
    cd run-adk-agent
    ```

    ```bash
    export PROJECT_ID=<your-gcp-project-id>
    export LOCATION=us-central1    
    ```

2.  **`terraform.tfvars` 업데이트:**
    Terraform 구성에 프로젝트 세부 정보를 주입합니다.

    ```bash
    sed -i \
    -e "s/your-gcp-project-id/${PROJECT_ID}/" \
    -e "s/your-location/${LOCATION}/" \
    ./terraform/terraform.tfvars
    ```

3.  **Terraform 초기화 및 적용:**

    ```bash
    terraform -chdir=terraform init
    terraform -chdir=terraform plan
    terraform -chdir=terraform apply --auto-approve
    ```

    **📝 출력 결과(Outputs) 확인:** 다음 단계에서 이 값들이 필요합니다.
    ```text
    network_name = "run-ai-apps-network"
    subnetwork_name = "run-ai-apps-subnet"
    service_account_account_id = "run-ai-apps-sa"
    ```

### 기본 배포 환경 구성

1.  **배포 환경 구성:**

    ```bash
    # Terraform 출력에서 리소스 정의
    export NETWORK_NAME=run-ai-apps-network
    export SUBNET_NAME=run-ai-apps-subnet

    export SERVICE_ACCOUNT=run-ai-apps-sa

    # 사용자 구성
    export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
    export MEMBER=$(gcloud config get-value account)

    export AGENT_NAME=zoo-concierge

    # AI 모델 구성
    export GEMINI_MODEL=gemini-2.5-flash
    
    ```

2.  **배포자 권한 부여:**

    실제 Cloud Run 에서 사용할 SA 생성과 SA 에 필요한 권한 부여는 Terraform 에서 이미 수행했습니다. 
    이 작업은 실제 환경 구성할때 필요한 권한을 현재 작업자가 사용하는 계정 (예를 들어 Qwiklab user 계정) 에 부여하는 작업입니다.

    ```bash
    # Cloud Run 관리자 역할 부여
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="user:$MEMBER" \
        --role="roles/run.admin"

    # 서비스 계정 사용자 역할 부여
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="user:$MEMBER" \
        --role="roles/iam.serviceAccountUser"

    # Cloud Build 편집자 역할 부여
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="user:$MEMBER" \
        --role="roles/cloudbuild.builds.editor"
    ```

3.  **Google ADK 설치:**

    참조: [ADK 설치 가이드](https://google.github.io/adk-docs/get-started/installation/)
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install google-adk
    ```

### MemoryBank 사용을 위한 AgentEngine 생성
Agent Engine을 프로비저닝하거나 삭제하는 스크립트도 이제 커맨드라인 인자를 통해 필요한 정보를 전달받습니다.

1.  **프로비저닝 스크립트 실행 (`provisioning.py`):**

    Agent Engine을 새로 생성할 때 사용합니다.

    ```bash
    python3 ./agentengine/provisioning.py \
      --project_id ${PROJECT_ID} \
      --location ${LOCATION} \
      --agent_name ${AGENT_NAME} \
      --model ${GEMINI_MODEL}
    ```

    나온 결과값을 `AGENT_ENGINE_ID` 에 설정합니다.
    ```bash
    export AGENT_ENGINE_ID=1348944636630007808
    ```

2.  **(Optional) 삭제 스크립트 실행 (`cleaning.py`):**

    기존에 생성된 Agent Engine을 삭제할 때 사용합니다.

    ```bash
    python3 ./agentengine/cleaning.py \
      --project_id ${PROJECT_ID} \
      --location ${LOCATION} \
      --agent_engine_id ${AGENT_ENGINE_ID}
    ```

### Cloud Run 에 MCP Server 배포

1.  **Zoo Animal MCP 서버 배포:**
    ```bash
    gcloud run deploy zoo-animal-mcp-server \
        --source ./zoo_animal_mcp_server/ \
        --region ${LOCATION} \
        --service-account ${SERVICE_ACCOUNT} \
        --no-allow-unauthenticated \
        --network=${NETWORK_NAME} \
        --subnet=${SUBNET_NAME} \
        --vpc-egress=all-traffic \
        --ingress internal
    ```

2.  **Zoo Show MCP 서버 배포:**
    ```bash
    gcloud run deploy zoo-show-mcp-server \
        --source ./zoo_show_mcp_server/ \
        --region ${LOCATION} \
        --service-account ${SERVICE_ACCOUNT} \
        --no-allow-unauthenticated \
        --network=${NETWORK_NAME} \
        --subnet=${SUBNET_NAME} \
        --vpc-egress=all-traffic \
        --ingress internal
    ```

3.  **에이전트 환경 구성 (.env):**
    에이전트가 MCP 서버의 위치와 Google Cloud 프로젝트 ID를 알 수 있도록 구성합니다.

    ```bash
    # Concierge Agent를 위한 .env 생성 (Animal MCP에 연결)
    echo "MCP_SERVER_URL=https://zoo-animal-mcp-server-${PROJECT_NUMBER}.${LOCATION}.run.app/mcp" >> ./zoo_concierge_agent/.env

    # Show Agent를 위한 .env 생성 (Show MCP에 연결)
    echo "MCP_SERVER_URL=https://zoo-show-mcp-server-${PROJECT_NUMBER}.${LOCATION}.run.app/mcp" >> ./zoo_show_agent/.env

    # .env 파일 내 프로젝트 ID 업데이트
    sed -i -e "s|your-gcp-project-id|${PROJECT_ID}|" ./zoo_concierge_agent/.env
    sed -i -e "s|your-gcp-project-id|${PROJECT_ID}|" ./zoo_show_agent/.env
    ```

### Cloud Run 에 ADK Agent 배포

1.  **Zoo Show Agent 배포 (A2A 대상):**
    이 에이전트는 쇼 예약이라는 전문 작업을 처리합니다.

    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${LOCATION} \
      --service_name=zoo-show-agent \
      --a2a \
      --artifact_service_uri=memory:// \
      ./zoo_show_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic
    ```

2.  **에이전트 연결:**
    A2A 프로토콜을 사용하여 배포된 `zoo_show_agent`를 가리키도록 `zoo_concierge_agent` 구성을 업데이트합니다.

    ```bash    
    cp ./zoo_show_agent/agent.json ./zoo_concierge_agent/agent.json
    ```
    ```bash
    # 배포된 URL로 에이전트 카드 업데이트
    sed -i -e "s|your_agent_server_url|https://zoo-show-agent-${PROJECT_NUMBER}.${LOCATION}.run.app/a2a/zoo_show_agent|" ./zoo_concierge_agent/agent.json
    ```

3.  **Zoo Concierge Agent 배포 (메인 진입점):**

    사용자가 상호 작용하는 메인 에이전트입니다.
    *   `Allow unauthenticated invocations to [zoo-concierge-agent] (y/N)?` 질문에 `y`를 입력하세요.

    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${LOCATION} \
      --service_name=zoo-concierge-agent \
      --with_ui \
      --session_service_uri=agentengine://${AGENT_ENGINE_ID} \
      --memory_service_uri=agentengine://${AGENT_ENGINE_ID} \
      --artifact_service_uri=memory:// \
      ./zoo_concierge_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic
    ```

## 🎮 사용 방법

배포가 완료되면 `adk deploy` 명령어가 제공한 URL을 통해 **Zoo Concierge Agent**에 액세스할 수 있습니다. 인터페이스를 통해 동물에 대해 질문하거나 쇼 예약을 요청할 수 있습니다.

단계별 가이드는 다음 코드랩을 참조하세요:
[Use MCP Server on Cloud Run with an ADK Agent](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent#8)

![AI Agent UI](./images/ai-agent-result.png)

## 📚 참조 및 리소스

-   **Codelab: Secure MCP Server on Cloud Run:** [Link](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run?hl=ko#6)
-   **Codelab: ADK Agent with MCP:** [Link](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent?hl=ko#0)

### 생성된 Terraform 리소스

`terraform/` 디렉토리에는 다음을 프로비저닝하는 스크립트가 포함되어 있습니다:

-   **네트워킹 (Networking):**
    -   `google_compute_network`: 격리를 위한 커스텀 VPC (`run-ai-apps-network`).
    -   `google_compute_subnetwork`: 리소스를 위한 서브넷 (`run-ai-apps-subnet`).
    -   `google_compute_router` & `google_compute_router_nat`: 외부 IP 없이 안전한 아웃바운드 인터넷 액세스를 위한 Cloud Router 및 NAT.
-   **보안 및 IAM (Security & IAM):**
    -   `google_service_account`: 에이전트를 위한 전용 ID (`run-ai-apps-sa`).
    -   `google_project_iam_member`: 서비스 계정에 할당된 세분화된 권한 (Vertex AI User, Cloud Run Invoker).
-   **비공개 연결 (Private Connectivity):**
    -   `google_compute_global_address` & `google_compute_global_forwarding_rule`: Private Service Connect (PSC) 설정.
    -   `google_dns_managed_zone` & `google_dns_record_set`: PSC를 통해 Google API 트래픽을 안전하게 라우팅하기 위한 비공개 DNS.
-   **서비스 (Services):**
    -   `google_project_service`: 필요한 API 활성화 (Cloud Run, Vertex AI, Cloud Build 등).

<br>
<img src="./images/terraform.png" width="800" alt="Terraform 리소스 다이어그램">