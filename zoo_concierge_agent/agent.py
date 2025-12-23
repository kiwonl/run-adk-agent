import os
import logging
from dotenv import load_dotenv

import google.cloud.logging
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.google_search_tool import GoogleSearchTool

# --- Setup Logging and Environment ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()
model_name = os.getenv("MODEL", "gemini-2.5-flash")
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise ValueError("The environment variable MCP_SERVER_URL is not set.")


def get_id_token():
    """Get an ID token to authenticate with the MCP server."""
    audience = mcp_server_url.split("/mcp")[0]
    request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    return id_token


# MCP Server Tool 설정
mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
        headers={
            "Authorization": f"Bearer {get_id_token()}",
        },
    ),
)


# Greet user and save their prompt
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}


# 1. Researcher Agent
comprehensive_researcher = Agent(
    name="comprehensive_researcher",
    model=model_name,
    description="The primary researcher that can access both internal zoo data and external knowledge from Google Search..",
    instruction="""
    You are a helpful research assistant. Your goal is to fully answer the user's PROMPT.
    You have access to two tools:
    1. A tool for getting specific data about animals AT OUR ZOO (names, ages, locations).
    2. A tool for google search for general knowledge (facts, lifespan, diet, habitat).

    First, analyze the user's PROMPT.
    - If the prompt can be answered by only one tool, use that tool.
    - If the prompt is complex and requires information from both the zoo's database AND google search,
      you MUST use them sequentially. First, use the zoo's database to get internal information.
      Once you have the result, THEN use google search for general knowledge.
      DO NOT call both tools at the same time.
    - Synthesize the results from the tool(s) you use into preliminary data outputs.
    """,
    tools=[mcp_tools, GoogleSearchTool(bypass_multi_tools_limit=True)],
    output_key="research_data",  # A key to store the combined findings
)

# 2. Response Formatter Agent
response_formatter = Agent(
    name="response_formatter",
    model=model_name,
    description="Synthesizes all information into a friendly, readable response.",
    instruction="""
    You are the friendly voice of the Zoo Tour Guide. Your task is to take the
    RESEARCH_DATA and present it to the user in a complete and helpful answer.

    - First, present the specific information from the zoo (like names, ages, and where to find them).
    - Then, add the interesting general facts from the research.
    - If some information is missing, just present the information you have.
    - Be conversational and engaging.

    RESEARCH_DATA:
    {{ research_data }}
    """,
)

# Sequancial Agent Workflow
zoo_concierge_agent = SequentialAgent(
    name="zoo_concierge_agent",
    description="Handles questions about animal information and knowledge.",
    sub_agents=[
        comprehensive_researcher,  # Step 1: Gather all data
        response_formatter,  # Step 2: Format the final response
    ],
)

# Remote Agents by A2A
current_dir = os.path.dirname(os.path.abspath(__file__))
# # zoo_concierge_agent 디렉토리의 상위 디렉토리로 가서 zoo_show_agent 디렉토리로 진입
agent_card_path = os.path.join(current_dir, "agent.json")
zoo_show_agent = RemoteA2aAgent(
    name="zoo_show_agent",
    description="Used to check animal show schedules or make show reservations.",
    agent_card=agent_card_path,
)

# Root Agent
root_agent = Agent(
    name="greeter",
    model=model_name,
    description="The main guide for the zoo. Calls the appropriate expert based on the user's intent.",
    instruction="""
    You are the zoo concierge. Analyze the user's input and forward it to the appropriate agent among the following:

    1. If the user asks for 'knowledge' such as animal ecology, information, or location, call 'zoo_concierge_agent'.
    2. If the user asks about animal shows or reservations of shows, call 'zoo_show_agent'.
    3. If the user simply greets or is ambiguous, greet them kindly and ask how you can help.
    """,
    tools=[add_prompt_to_state],
    sub_agents=[zoo_concierge_agent, zoo_show_agent],
)
