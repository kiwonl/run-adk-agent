import argparse
import os
import vertexai

parser = argparse.ArgumentParser(description="Delete an Agent Engine")
parser.add_argument("--project_id", type=str, help="Google Cloud Project ID", required=True)
parser.add_argument("--location", type=str, help="Google Cloud Location", required=True)
parser.add_argument("--agent_engine_id", type=str, help="Agent Engine ID", required=True)

args = parser.parse_args()

PROJECT_ID = args.project_id
LOCATION = args.location
AGENT_ENGINE_ID = args.agent_engine_id

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

# Construct the full resource name using the correct "reasoningEngines"
resource_name = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
)

print(f"Deleting Agent Engine: {resource_name}...")

try:
    operation = client.agent_engines.delete(name=resource_name, force=True)
    # Wait for the operation to complete if it returns an operation object
    if hasattr(operation, "result"):
        operation.result()
    print(f"Successfully deleted Agent Engine: {AGENT_ENGINE_ID}")
except Exception as e:
    print(f"Failed to delete Agent Engine: {e}")
