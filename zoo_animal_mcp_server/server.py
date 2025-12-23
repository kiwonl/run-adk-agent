import asyncio
import logging
import os
import json
from typing import List, Dict, Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server for zoo animal data.
mcp = FastMCP("Zoo Animal MCP Server 🦁🐧🐻")

# Global Data Stores
ZOO_ANIMALS: List[Dict[str, Any]] = []
# Index for querying by species (e.g., "lion" -> [Leo, Nala...], "사자" -> [Leo, Nala...])
ZOO_ANIMALS_BY_SPECIES: Dict[str, List[Dict[str, Any]]] = {}


def load_zoo_data():
    """Loads zoo animal data from JSON and builds species-based indexes."""
    global ZOO_ANIMALS, ZOO_ANIMALS_BY_SPECIES

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "zoo_animals.json")

    try:
        logger.info(f"📖 Loading zoo data from {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_animals = json.load(f)
            ZOO_ANIMALS = loaded_animals

        # Build index for O(1) lookup by species (English and Korean)
        ZOO_ANIMALS_BY_SPECIES = {}
        for animal in ZOO_ANIMALS:
            species_en = animal.get("species", "").lower()
            species_kr = animal.get("species_kr", "")

            # Index by English species name
            if species_en:
                if species_en not in ZOO_ANIMALS_BY_SPECIES:
                    ZOO_ANIMALS_BY_SPECIES[species_en] = []
                ZOO_ANIMALS_BY_SPECIES[species_en].append(animal)

            # Index by Korean species name
            if species_kr:
                if species_kr not in ZOO_ANIMALS_BY_SPECIES:
                    ZOO_ANIMALS_BY_SPECIES[species_kr] = []
                ZOO_ANIMALS_BY_SPECIES[species_kr].append(animal)

        logger.info(
            f"✅ Successfully loaded {len(ZOO_ANIMALS)} animals across {len(ZOO_ANIMALS_BY_SPECIES)} species keys."
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error loading data: {e}")
        ZOO_ANIMALS = []
        ZOO_ANIMALS_BY_SPECIES = {}


# Load data on startup
load_zoo_data()


@mcp.tool()
def get_animals_by_species(species: str) -> List[Dict[str, Any]]:
    """
    Retrieves a list of animals belonging to a specific species.
    Args:
        species: The species name in English (e.g., 'lion') or Korean (e.g., '사자').
    """
    logger.info(f">>> 🛠️ Tool: 'get_animals_by_species' called for '{species}'")
    # O(1) Lookup using the pre-built index
    return ZOO_ANIMALS_BY_SPECIES.get(species.lower(), [])


@mcp.tool()
def list_available_species() -> List[str]:
    """
    Retrieves a list of all unique animal species available in the zoo (English names only).
    """
    logger.info(">>> 🛠️ Tool: 'list_available_species' called")
    unique_species = set()
    for animal in ZOO_ANIMALS:
        if "species" in animal:
            unique_species.add(animal["species"])
    return sorted(list(unique_species))


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
