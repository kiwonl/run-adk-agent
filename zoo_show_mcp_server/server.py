import asyncio
import logging
import os

import json
from typing import List, Dict, Any, Optional


from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Initialize FastMCP server for zoo show data.
mcp = FastMCP("Zoo Show MCP Server 🎟️")

# Global Data Stores
ZOO_SHOWS: List[Dict[str, Any]] = []
ZOO_SHOWS_BY_NAME: Dict[str, Dict[str, Any]] = {}


# Loads show data from a JSON file and creates an in-memory index.
def load_show_data():
    """Loads zoo show data from JSON and builds indexes."""
    global ZOO_SHOWS, ZOO_SHOWS_BY_NAME

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "zoo_shows.json")

    try:
        logger.info(f"Loading zoo show data from {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_shows = json.load(f)
            ZOO_SHOWS = loaded_shows

        # Build index for O(1) lookup
        ZOO_SHOWS_BY_NAME = {show["name"].lower(): show for show in ZOO_SHOWS}

        logger.info(f"Successfully loaded {len(ZOO_SHOWS)} shows.")

    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        ZOO_SHOWS = []
        ZOO_SHOWS_BY_NAME = {}


# Load data on startup
load_show_data()


@mcp.tool()
def get_shows_by_animal(animal_name: str) -> List[Dict[str, Any]]:
    # MCP tool to filter shows based on animal name.
    logger.info(f">>> 🛠️ Tool: 'filter_shows_by_animal' called for '{animal_name}'")
    animal_lower = animal_name.lower()
    return [
        show
        for show in ZOO_SHOWS
        if animal_lower in show["name"].lower()
        or animal_lower in show["description"].lower()
        or (show.get("animal") and animal_lower == show["animal"].lower())
    ]


@mcp.tool()
def get_show_details(name: str) -> Optional[Dict[str, Any]]:
    # MCP tool to retrieve details of a specific show by name.
    logger.info(f">>> 🛠️ Tool: 'get_show_details' called for '{name}'")
    return ZOO_SHOWS_BY_NAME.get(name.lower())


# Entry point for running the MCP server.
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 MCP server started on port {port}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
