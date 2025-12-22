# AI 에이전트 인프라 설정

## 개요

이 프로젝트는 Google Cloud에 정교한 AI 에이전트를 배포하기 위한 포괄적인 설정을 제공합니다. 이 에이전트는 가상의 동물원의 동물에 대한 질문에 답할 수 있는 "동물원 투어 가이드"로 설계되었습니다. 동물원 특정 데이터에는 자체 구축한 MCP(Multi-turn Conversation Platform) 서버를 활용하고, 일반 지식에는 위키백과를 활용합니다. 전체 인프라는 Terraform을 사용하여 관리되며, 에이전트는 Cloud Run에 배포됩니다.

![ai-agent-design](./images/ai-agent-design.png)

## 시작하기

## Terraform을 통한 인프라 설정

1.  **환경 변수 설정:**

    다음 지침은 `run-ai-apps` 디렉터리의 루트에서 시작한다고 가정합니다.

    ```bash
    cd ~/run-adk-agent

    export PROJECT_ID=<your-gcp-project-id>
    export REGION=us-central1
    ```

2.  **`terraform.tfvars` 업데이트:**

    ```bash
    sed -i \
    -e "s/your-gcp-project-id/$PROJECT_ID/" \
    -e "s/your-region/$REGION/" \
    ./terraform/terraform.tfvars
    ```

3.  **Terraform 초기화 및 적용:**

    -chdir : terraform 폴더에 있는 것 처럼 동작해라.
    ```bash
    terraform -chdir=terraform init
    terraform -chdir=terraform plan
    terraform -chdir=terraform apply --auto-approve
    ```

    출력 결과(Outputs)를 기록해 두세요.
    ```
    Outputs:

    network_name = "run-ai-apps-network"
    subnetwork_name = "run-ai-apps-subnet"
    service_account_account_id = "run-ai-apps-sa"
    ```

### Cloud Run에 애플리케이션 배포

1.  **Terraform 출력에서 환경 변수 설정:**

    ```bash
    # Terraform 으로 생성된 리소스의 이름을 정의
    export NETWORK_NAME=run-ai-apps-network
    export SUBNET_NAME=run-ai-apps-subnet
    export SERVICE_ACCOUNT=run-ai-apps-sa

    # 사용자의 GCP 사용자 이름, `gcloud auth list`를 통해 확인할 수 있습니다.
    export MEMBER=<your-gcp-user-name>
    export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")  

    # 사용할 AI Model 정의 (gemini-3-pro-preview)
    export GEMINI_MODEL=gemini-2.5-flash
    ```

2.  **배포자 권한 부여 (귀하의 계정에 대한 일회성 설정):**

    `gcloud run deploy`를 실행하는 사용자 계정은 서비스를 배포하고, 서비스 계정을 할당하고, 백그라운드에서 Cloud Build를 사용하기 위한 권한이 필요합니다. 현재 로그인된 `gcloud` 사용자에게 이러한 역할을 부여하려면 다음 명령어를 실행하십시오.

    ```bash
    # Cloud Run 서비스 배포 및 관리를 위한 권한 부여
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/run.admin"

    # 서비스 계정을 Cloud Run 서비스와 연결하기 위한 권한 부여
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/iam.serviceAccountUser"

    # 업로드된 소스 코드로부터 빌드를 트리거하기 위한 권한 부여
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/cloudbuild.builds.editor"
    ```

3.  **Zoo Animal MCP 서버 배포:**

    이 명령어는 소스 코드로부터 컨테이너 이미지를 빌드하고 Cloud Run에 배포합니다.

    ```bash
    gcloud run deploy zoo-animal-mcp-server \
        --source ./zoo_aminal_mcp_server/ \
        --region ${REGION} \
        --service-account ${SERVICE_ACCOUNT} \
        --no-allow-unauthenticated \
        --network=${NETWORK_NAME} \
        --subnet=${SUBNET_NAME} \
        --vpc-egress=all-traffic \
        --ingress internal
    ```

4.  **Zoo Show MCP 서버 배포:**

    이 명령어는 소스 코드로부터 컨테이너 이미지를 빌드하고 Cloud Run에 배포합니다.

    ```bash
    gcloud run deploy zoo-show-mcp-server \
        --source ./zoo_show_mcp_server/ \
        --region ${REGION} \
        --service-account ${SERVICE_ACCOUNT} \
        --no-allow-unauthenticated \
        --network=${NETWORK_NAME} \
        --subnet=${SUBNET_NAME} \
        --vpc-egress=all-traffic \
        --ingress internal
    ```

4.  **.env 파일 업데이트:**
    ```bash
    echo -e "\nMCP_SERVER_URL=https://zoo-animal-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/" >> ./zoo_aminal_mcp_server/.env    
    echo -e "\nMCP_SERVER_URL=https://zoo-show-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/" >> ./zoo_show_mcp_server/.env
    ```

5.  **로컬 환경에 Google ADK 설치:**

    참조: [ADK 설치 가이드](https://google.github.io/adk-docs/get-started/installation/)
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install google-adk
    ```

6.  **Zoo_shot_agconcierge_agent 배포:**

    `Allow unauthenticated invocations to [zoo-tour-guide] (y/N)?` 메시지가 나타나면 `y`를 입력하십시오.
    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${REGION} \
      --service_name=zoo-show-agent \
      --with_ui \
      --a2a \
      ./zoo_show_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic
    ```

4.  **.env 파일 업데이트:**
    ```bash
    cp ./zoo_show_agent/agent.py ./zoo_concierge_agent/agent.py           
    sed -i -e "s/your_agent_server_url/https://zoo-show-agent-${PROJECT_NUMBER}.${REGION}.run.app/" ./zoo_show_agent/agent.json
    ```

7.  **Zoo_concierge_agent 배포:**

    `Allow unauthenticated invocations to [zoo-tour-guide] (y/N)?` 메시지가 나타나면 `y`를 입력하십시오.
    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${REGION} \
      --service_name=zoo-concierge-agent \
      --with_ui \
      ./zoo_concierge_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic

    ```


## 사용법
자세한 사용법은 다음 코드랩을 참조하십시오:
https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent#8

![AI Agent UI](./images/ai-agent-result.png)

## AI 에이전트 소스 코드 참조 

- [MCP 서버 코드랩](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run?hl=ko#6)
- [AI 에이전트 코드랩](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent?hl=ko#0)

## Terraform 리소스

`terraform` 디렉터리의 Terraform 스크립트는 다음 Google Cloud 리소스를 생성합니다:

-   **`google_project_service`**: Cloud Run, Vertex AI, Cloud DNS, Service Directory, Cloud Build, Artifact Registry 등 프로젝트에 필요한 Google Cloud API를 활성화합니다.
-   **`google_service_account`**: Cloud Run 서비스가 다른 Google Cloud 서비스와 안전하게 상호 작용할 수 있도록 전용 서비스 계정(`run-ai-apps-sa`)을 생성합니다.
-   **`google_project_iam_member`**: 서비스 계정에 `roles/aiplatform.user` 및 `roles/run.invoker`와 같은 필요한 IAM 역할을 할당하여 다른 Google Cloud 서비스와 상호 작용할 수 있도록 합니다.
-   **`google_compute_network`**: 서비스에 안전하고 격리된 환경을 제공하기 위해 사용자 지정 Virtual Private Cloud (VPC) 네트워크(`run-ai-apps-network`)를 생성합니다.
-   **`google_compute_subnetwork`**: VPC 내에 서브네트워크(`run-ai-apps-subnet`)를 생성합니다.
-   **`google_compute_router`**: VPC 네트워크의 동적 라우팅을 관리하기 위해 Cloud Router를 생성합니다.
-   **`google_compute_router_nat`**: 외부 IP 주소가 없는 인스턴스가 인터넷에 액세스할 수 있도록 Cloud NAT 게이트웨이를 생성합니다.
-   **`google_compute_global_address`**: Private Service Connect (PSC)를 위해 전역 내부 IP 주소를 예약하여 Google API에 대한 비공개 액세스를 활성화합니다.
-   **`google_compute_global_forwarding_rule`**: PSC를 통해 예약된 IP 주소에서 Google API로 트래픽을 전달하는 전달 규칙을 생성합니다.
-   **`google_dns_managed_zone`**: `googleapis.com`에 대한 비공개 DNS 영역을 생성하여 Google API 도메인 이름을 PSC 엔드포인트로 확인(resolve)합니다.
-   **`google_dns_record_set`**: 비공개 영역 내에 PSC 엔드포인트를 가리키는 DNS 레코드를 생성합니다.
    <BR><BR><img src="./images/terraform.png" width="800">
