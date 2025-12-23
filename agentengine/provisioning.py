# https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-api#generate-memories
import argparse
import os
import vertexai

from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService

from google.adk.runners import Runner
from google.genai import types

parser = argparse.ArgumentParser(description="Provision an Agent Engine")
parser.add_argument("--project_id", type=str, help="Google Cloud Project ID", required=True)
parser.add_argument("--location", type=str, help="Google Cloud Location", required=True)
parser.add_argument("--agent_name", type=str, help="Name of the Agent", required=True)
parser.add_argument("--model", type=str, help="Model to use", required=True)

args = parser.parse_args()

PROJECT_ID = args.project_id
LOCATION = args.location
AGENT_NAME = args.agent_name
MODEL = args.model

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
agent_engine = client.agent_engines.create(
    config={
        "display_name": AGENT_NAME,
        "context_spec": {
            "memory_bank_config": {
                "generation_config": {
                    "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}"
                }
            }
        },
    }
)

agent_engine_id = agent_engine.api_resource.name.split("/")[-1]
print(agent_engine_id)