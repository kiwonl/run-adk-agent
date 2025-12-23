# AI Agent Infrastructure on Google Cloud Run

## 🌟 Overview

This project provides a comprehensive setup for deploying sophisticated, multi-agent AI systems on Google Cloud Platform (GCP). It demonstrates a real-world use case: a **Zoo Concierge System** designed to assist visitors with animal information and show bookings.

The architecture leverages cutting-edge technologies to create a scalable and secure agent ecosystem:
*   **zoo_concierge_agent**: The main entry point for users. It handles general inquiries using a "Researcher" sub-agent (connected to an MCP server for zoo data and Google Search for general facts) and routes booking requests to a specialized agent.
*   **zoo_show_agent**: A specialized agent dedicated to managing show schedules and reservations. It communicates with the main agent via the **A2A (Agent-to-Agent)** protocol.
*   **MCP Servers**: Two custom **Model Context Protocol (MCP)** servers (`zoo_animal_mcp_server` and `zoo_show_mcp_server`) provide structured access to proprietary zoo data, decoupled from the agent logic.

The entire infrastructure is provisioned using **Terraform**, ensuring a secure, production-ready environment with VPCs, private networking, and IAM policies, all deployed on **Google Cloud Run**.

![ai-agent-design](./images/ai-agent-design.png)

## 🚀 Key Technologies

*   **Google Cloud Run**: A fully managed serverless platform for deploying highly scalable containerized applications.
*   **Model Context Protocol (MCP)**: An open standard that enables AI models to securely connect to external data sources and tools.
*   **Google ADK (Agent Development Kit)**: A Python framework for building, testing, and deploying GenAI agents.
*   **A2A (Agent-to-Agent) Protocol**: A mechanism allowing independent agents to discover and interact with each other to solve complex tasks collaboratively.
*   **Terraform**: Infrastructure as Code (IaC) tool to define and provision the cloud resources consistently.

---

## 🛠️ Getting Started

### Prerequisites
*   Google Cloud Platform (GCP) Project
*   `gcloud` CLI installed and authenticated
*   `terraform` installed
*   Python 3.10+

### Infrastructure Setup with Terraform

1.  **Set Environment Variables:**
    Start from the root of the `run-adk-agent` directory.
    
    ```bash
    cd run-adk-agent
    ```

    ```bash
    export PROJECT_ID=<your-gcp-project-id>
    export REGION=us-central1
    ```

2.  **Update `terraform.tfvars`:**
    Inject your project details into the Terraform configuration.

    ```bash
    sed -i \
    -e "s/your-gcp-project-id/$PROJECT_ID/" \
    -e "s/your-region/$REGION/" \
    ./terraform/terraform.tfvars
    ```

3.  **Initialize and Apply Terraform:**

    ```bash
    terraform -chdir=terraform init
    terraform -chdir=terraform plan
    terraform -chdir=terraform apply --auto-approve
    ```

    **📝 Note the Outputs:** You will need these values for the next steps.
    ```text
    network_name = "run-ai-apps-network"
    subnetwork_name = "run-ai-apps-subnet"
    service_account_account_id = "run-ai-apps-sa"
    ```

### Application Deployment to Cloud Run

1.  **Configure Deployment Environment:**

    ```bash
    # Define resources from Terraform outputs
    export NETWORK_NAME=run-ai-apps-network
    export SUBNET_NAME=run-ai-apps-subnet
    export SERVICE_ACCOUNT=run-ai-apps-sa

    # User configuration
    export MEMBER=$(gcloud config get-value account)
    export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

    # AI Model configuration
    export GEMINI_MODEL=gemini-2.5-flash
    ```

2.  **Grant Deployer Permissions (One-time Setup):**
    Ensure your user account has the necessary permissions to build and deploy to Cloud Run.

    ```bash
    # Grant Cloud Run Admin role
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/run.admin"

    # Grant Service Account User role
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/iam.serviceAccountUser"

    # Grant Cloud Build Editor role
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:$MEMBER" \
        --role="roles/cloudbuild.builds.editor"
    ```

3.  **Deploy MCP Servers:**

    **Deploy Zoo Animal MCP Server:**
    ```bash
    gcloud run deploy zoo-animal-mcp-server \
        --source ./zoo_animal_mcp_server/ \
        --region ${REGION} \
        --service-account ${SERVICE_ACCOUNT} \
        --no-allow-unauthenticated \
        --network=${NETWORK_NAME} \
        --subnet=${SUBNET_NAME} \
        --vpc-egress=all-traffic \
        --ingress internal
    ```

    **Deploy Zoo Show MCP Server:**
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

4.  **Configure Agent Environment (.env):**
    Configure the agents with the MCP server URLs and your Google Cloud Project ID.

    ```bash
    # Create .env for Concierge Agent (connects to Animal MCP)
    echo "MCP_SERVER_URL=https://zoo-animal-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp" >> ./zoo_concierge_agent/.env

    # Create .env for Show Agent (connects to Show MCP)
    echo "MCP_SERVER_URL=https://zoo-show-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp" >> ./zoo_show_agent/.env

    # Update Project ID in .env files
    sed -i -e "s|your-gcp-project-id|${PROJECT_ID}|" ./zoo_concierge_agent/.env
    sed -i -e "s|your-gcp-project-id|${PROJECT_ID}|" ./zoo_show_agent/.env
    ```

5.  **Install Google ADK:**

    Reference: [ADK Installation Guide](https://google.github.io/adk-docs/get-started/installation/)
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install google-adk
    ```

6.  **Deploy Zoo Show Agent (A2A Target):**

    This agent handles the specialized task of booking shows.
    *   Type `y` when asked `Allow unauthenticated invocations to [zoo-show-agent] (y/N)?`

    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${REGION} \
      --service_name=zoo-show-agent \
      --a2a \
      --with_ui \
      --artifact_service_uri=memory:// \
      ./zoo_show_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic
    ```

7.  **Connect Agents:**
    Update the `zoo_concierge_agent` configuration to point to the deployed `zoo_show_agent` using the A2A protocol.

    ```bash    
    cp ./zoo_show_agent/agent.json ./zoo_concierge_agent/agent.json
    ```
    ```bash
    # Update the Agent Card with the deployed URL
    sed -i -e "s|your_agent_server_url|https://zoo-show-agent-${PROJECT_NUMBER}.${REGION}.run.app/a2a/zoo_show_agent|" ./zoo_concierge_agent/agent.json
    ```

8.  **Deploy Zoo Concierge Agent (Main Entry):**

    This is the main agent users interact with.
    *   Type `y` when asked `Allow unauthenticated invocations to [zoo-concierge-agent] (y/N)?`

    ```bash
    adk deploy cloud_run \
      --project=${PROJECT_ID} \
      --region=${REGION} \
      --service_name=zoo-concierge-agent \
      --with_ui \
      --artifact_service_uri=memory:// \
      ./zoo_concierge_agent \
      -- --allow-unauthenticated \
      --service-account ${SERVICE_ACCOUNT} \
      --network=${NETWORK_NAME} \
      --subnet=${SUBNET_NAME}  \
      --vpc-egress=all-traffic
    ```

## 🎮 Usage

Once deployed, you can access the **Zoo Concierge Agent** via the URL provided by the `adk deploy` command. The interface allows you to ask questions about animals or request show bookings.

For a guided walkthrough, refer to the codelab:
[Use MCP Server on Cloud Run with an ADK Agent](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent#8)

![AI Agent UI](./images/ai-agent-result.png)

## 📚 References & Resources

-   **Codelab: Secure MCP Server on Cloud Run:** [Link](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run?hl=ko#6)
-   **Codelab: ADK Agent with MCP:** [Link](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent?hl=ko#0)

### Terraform Resources Created

The `terraform/` directory contains scripts that provision the following:

-   **Networking:**
    -   `google_compute_network`: A custom VPC (`run-ai-apps-network`) for isolation.
    -   `google_compute_subnetwork`: A subnet (`run-ai-apps-subnet`) for the resources.
    -   `google_compute_router` & `google_compute_router_nat`: Cloud Router and NAT for secure outbound internet access without external IPs.
-   **Security & IAM:**
    -   `google_service_account`: A dedicated identity (`run-ai-apps-sa`) for the agents.
    -   `google_project_iam_member`: Granular permissions (Vertex AI User, Cloud Run Invoker) assigned to the service account.
-   **Private Connectivity:**
    -   `google_compute_global_address` & `google_compute_global_forwarding_rule`: Setup for Private Service Connect (PSC).
    -   `google_dns_managed_zone` & `google_dns_record_set`: Private DNS to route Google API traffic securely via PSC.
-   **Services:**
    -   `google_project_service`: Enables necessary APIs (Cloud Run, Vertex AI, Cloud Build, etc.).

<br>
<img src="./images/terraform.png" width="800" alt="Terraform Resource Diagram">