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
from google.adk.agents.callback_context import CallbackContext

from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from .callback_logging import log_query_to_model, log_model_response

# Setup Logging
google.cloud.logging.Client().setup_logging()
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Setup Environment
load_dotenv()
model_name = os.getenv("MODEL")
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise ValueError("The environment variable MCP_SERVER_URL is not set.")


# Helper to generate ID tokens for MCP server authentication.
def get_id_token():
    audience = mcp_server_url.split("/mcp")[0]
    request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    logger.info("🔑 Successfully generated ID token.")
    return id_token


# Configures MCPToolset for the animal data server.
mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
        headers={
            "Authorization": f"Bearer {get_id_token()}",
        },
    ),
)


# Tool to save the initial user prompt to the agent's state.
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    tool_context.state["PROMPT"] = prompt
    logging.info(f"📝 [State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}


# Callback to automatically save the session to memory after agent execution.
async def auto_save_session_to_memory_callback(callback_context: CallbackContext):
    try:
        inv_ctx = getattr(callback_context, "_invocation_context", None)
        if not inv_ctx or not inv_ctx.memory_service:
            logger.warning("⚠️ Memory Service not set, skipping memory save.")
            return

        logger.info(f"💾 Saving session {inv_ctx.session.id} to memory...")
        added_memories = await inv_ctx.memory_service.add_session_to_memory(
            inv_ctx.session
        )

        if added_memories:
            logger.info(f"✨ Saved Memory Content: {added_memories}")
        else:
            logger.info("🚫 No new memories generated.")

    except Exception as e:
        logger.error(f"❌ Error saving memory: {e}", exc_info=True)


# Agent for researching animal facts from internal and external sources.
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
    - Check if the requested animal exists in our zoo using the zoo database tool FIRST.
    - If the animal exists in the zoo:
        - Get the internal data (names, ages, locations).
        - Then, use google search for general knowledge if needed.
        - Synthesize the results.
    - If the animal DOES NOT exist in the zoo:
        - Explicitly state that "This animal is currently not in our zoo, so I cannot provide information about it."
        - DO NOT provide general information or use google search for animals not in the zoo.
    
    PROMPT:
    {{ PROMPT }}
        
    You MUST prioritize the zoo's internal data. Only provide information for animals present in the zoo.
    """,
    tools=[mcp_tools, GoogleSearchTool(bypass_multi_tools_limit=True)],
    output_key="research_data",  # A key to store the combined findings
)


# Agent for formatting research data into a friendly user response.
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

    All responses must be in Korean.
    You MUST only provide information about animals currently in our zoo, as known through the zoo_animal_mcp_server.

    RESEARCH_DATA:
    {{ research_data }}
    """,
)


# Sequential agent for handling animal information queries.
zoo_concierge_agent = SequentialAgent(
    name="zoo_concierge_agent",
    description="Handles questions about animal information and knowledge.",
    sub_agents=[
        comprehensive_researcher,  # Step 1: Gather all data
        response_formatter,  # Step 2: Format the final response
    ],
)

# Remote agent for handling show inquiries and bookings via A2A.
current_dir = os.path.dirname(os.path.abspath(__file__))
zoo_show_agent = RemoteA2aAgent(
    name="zoo_show_agent",
    description="Used to check animal show schedules or make show reservations.",
    agent_card=os.path.join(current_dir, "agent.json"),
)


# Root agent for orchestrating overall user interactions and routing.
root_agent = Agent(
    name="greeter",
    model=model_name,
    description="The main guide for the zoo. Calls the appropriate expert based on the user's intent.",
    instruction="""
    You are the zoo concierge.

    **CRITICAL STEP:**
    Before routing the request, you MUST FIRST use the `add_prompt_to_state` tool to save the user's input.
    Pass the user's exact input as the `prompt` argument.

    Then, analyze the input and forward it to the appropriate agent:

    1. If the user asks for 'knowledge' such as animal ecology, information, or location, call 'zoo_concierge_agent'.
    2. If the user asks about animal shows or reservations of shows, call 'zoo_show_agent'.
    3. If the user simply greets or is ambiguous, greet them kindly and ask how you can help.

    All responses must be in Korean.
    """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    after_agent_callback=auto_save_session_to_memory_callback,
    tools=[add_prompt_to_state, PreloadMemoryTool()],
    sub_agents=[zoo_concierge_agent, zoo_show_agent],
)
