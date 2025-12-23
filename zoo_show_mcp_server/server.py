import asyncio
import logging
import os
import json
from typing import List, Dict, Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Initialize FastMCP server for zoo show data.
mcp = FastMCP("Zoo Show MCP Server 🎟️")

# Global Data Stores
ZOO_SHOWS: List[Dict[str, Any]] = []
# Index for querying shows by species (e.g., "lion" -> [Show1, Show2...], "사자" -> [Show1...])
ZOO_SHOWS_BY_SPECIES: Dict[str, List[Dict[str, Any]]] = {}


def load_show_data():
    """Loads zoo show data from JSON and builds species-based indexes."""
    global ZOO_SHOWS, ZOO_SHOWS_BY_SPECIES

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "zoo_shows.json")

    try:
        logger.info(f"📂 Loading zoo show data from {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_shows = json.load(f)
            ZOO_SHOWS = loaded_shows

        # Build index for O(1) lookup by species (English and Korean)
        ZOO_SHOWS_BY_SPECIES = {}
        for show in ZOO_SHOWS:
            species_en = show.get("species", "").lower()
            species_kr = show.get("species_kr", "")

            # Index by English species name
            if species_en:
                if species_en not in ZOO_SHOWS_BY_SPECIES:
                    ZOO_SHOWS_BY_SPECIES[species_en] = []
                ZOO_SHOWS_BY_SPECIES[species_en].append(show)

            # Index by Korean species name
            if species_kr:
                if species_kr not in ZOO_SHOWS_BY_SPECIES:
                    ZOO_SHOWS_BY_SPECIES[species_kr] = []
                ZOO_SHOWS_BY_SPECIES[species_kr].append(show)

        logger.info(
            f"✅ Successfully loaded {len(ZOO_SHOWS)} shows across {len(ZOO_SHOWS_BY_SPECIES)} species keys."
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error loading data: {e}")
        ZOO_SHOWS = []
        ZOO_SHOWS_BY_SPECIES = {}


# Load data on startup
load_show_data()


@mcp.tool()
def get_shows_by_species(species: str) -> List[Dict[str, Any]]:
    """
    Retrieves a list of shows featuring a specific species.
    Args:
        species: The species name in English (e.g., 'lion') or Korean (e.g., '사자').
    """
    logger.info(f">>> 🛠️ Tool: 'get_shows_by_species' called for '{species}'")
    # O(1) Lookup using the pre-built index
    return ZOO_SHOWS_BY_SPECIES.get(species.lower(), [])


@mcp.tool()
def list_available_shows() -> List[str]:
    """
    Retrieves a list of all unique show names available in the zoo.
    """
    logger.info(">>> 🛠️ Tool: 'list_available_shows' called")
    unique_shows = set()
    for show in ZOO_SHOWS:
        if "name" in show:
            unique_shows.add(show["name"])
    return sorted(list(unique_shows))


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