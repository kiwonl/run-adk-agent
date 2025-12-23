import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

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
    target_url = os.getenv("MCP_SERVER_URL")
    audience = target_url.split("/mcp")[0]
    request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)

    logger.info("🔑 Successfully generated ID token.")
    return id_token


# Configures MCPToolset for the show data server.
mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
        headers={
            "Authorization": f"Bearer {get_id_token()}",
        },
    ),
)


# Root agent for handling show inquiries and bookings.
root_agent = Agent(
    name="zoo_show_agent",
    model=model_name,
    description="An agent that helps users find and book zoo shows.",
    instruction="""
    You are the Show Concierge and Booking Agent for Zoo.
    Your goal is to assist users in finding interesting animal shows and making reservations.

    **Workflow:**
    1.  **Information Gathering:**
        - When a user asks about shows (e.g., "I want to see a giraffe show"), use the available MCP tools (`get_shows_by_animal`, `get_show_details`) to find relevant shows.
        - Present the details (time, description, location) to the user.

    2.  **Booking Proposal:**
        - After presenting the information, ask the user if they would like to make a reservation for that show.

    3.  **Reservation:**
        - If the user says "yes" or wants to book:
            - Ask for the number of people (if not already provided).
            - Once you have the show name and the number of people, use the `reserve_show` tool to complete the booking.
            - **Confirmation Output:**
                - After a successful reservation, you MUST respond with a formatted message containing the following details using the information you gathered in step 1:
                    - **Show Name**: [Name of the show]
                    - **Start Time**: [Start time of the show]
                    - **Duration**: [Duration of the show]
                    - **Reserved Count**: [Number of people]
                    - **Notice**: Please arrive 10 minutes early. No outside food or drinks allowed.

    **Tone:**
    - Helpful, enthusiastic, and polite.
    """,
    tools=[mcp_tools],
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)
