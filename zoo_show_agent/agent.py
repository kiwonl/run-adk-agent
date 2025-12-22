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

# --- Setup Logging and Environment ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

# --- Configuration ---
model_name = os.getenv("MODEL", "gemini-2.5-flash")

# zoo_show_mcp_server 에 연결하도록 MCP 도구 구성
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise ValueError("The environment variable MCP_SERVER_URL is not set.")


def get_id_token():
    """Get an ID token to authenticate with the MCP server."""
    target_url = os.getenv("MCP_SERVER_URL")
    audience = target_url.split("/mcp/")[0]
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


# --- Tools ---
def reserve_show(show_name: str, count: int) -> str:
    """
    Reserves tickets for a specific zoo show.

    Args:
        show_name: The name of the show to reserve.
        count: The number of tickets/people.

    Returns:
        A confirmation message.
    """
    # In a real app, this would call a backend API or database.
    return f"Reservation confirmed: {count} tickets for '{show_name}'."


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
            - Confirm the reservation to the user with the result from the tool.

    **Tone:**
    - Helpful, enthusiastic, and polite.
    """,
    tools=[reserve_show, mcp_tools],
)
