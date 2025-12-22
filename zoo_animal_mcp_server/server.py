import asyncio
import logging
import os

import json
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Zoo Animal MCP Server 🦁🐧🐻")

# Global Data Stores
ZOO_ANIMALS: List[Dict[str, Any]] = []
ZOO_ANIMALS_BY_NAME: Dict[str, Dict[str, Any]] = {}


def load_zoo_data():
    """Loads zoo animal data from JSON and builds indexes."""
    global ZOO_ANIMALS, ZOO_ANIMALS_BY_NAME

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "zoo_animals.json")

    try:
        logger.info(f"Loading zoo data from {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_animals = json.load(f)
            ZOO_ANIMALS = loaded_animals  # Reassign the global list

        # Build index for O(1) lookup
        ZOO_ANIMALS_BY_NAME = {animal["name"].lower(): animal for animal in ZOO_ANIMALS}

        logger.info(f"Successfully loaded {len(ZOO_ANIMALS)} animals.")

    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        ZOO_ANIMALS = []
        ZOO_ANIMALS_BY_NAME = {}


# Load data on startup
load_zoo_data()


@mcp.tool()
def get_animals_by_species(species: str) -> List[Dict[str, Any]]:
    """
    Retrieves all animals of a specific species from the zoo.
    Can also be used to collect the base data for aggregate queries
    of animals of a specific species - like counting the number of penguins
    or finding the oldest lion.

    Args:
        species: The species of the animal (e.g., 'lion', 'penguin', '사자', '펭귄').

    Returns:
        A list of dictionaries, where each dictionary represents an animal
        and contains details like name, age, enclosure, and trail.
    """
    logger.info(f">>> 🛠️ Tool: 'get_animals_by_species' called for '{species}'")
    return [
        animal
        for animal in ZOO_ANIMALS
        if animal["species"].lower() == species.lower()
        or animal["species_kr"].lower() == species.lower()
    ]


@mcp.tool()
def get_animal_details(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of a specific animal by its name.

    Args:
        name: The name of the animal.

    Returns:
        A dictionary with the animal's details (species, species_kr, name, age, enclosure, trail)
        or None if the animal is not found.
    """
    logger.info(f">>> 🛠️ Tool: 'get_animal_details' called for '{name}'")
    # O(1) Lookup
    return ZOO_ANIMALS_BY_NAME.get(name.lower())


@mcp.tool()
def get_all_unique_animals() -> List[str]:
    """
    Retrieves a unique list of all animal names currently in the zoo.

    Returns:
        A list of unique animal names (strings).
    """
    logger.info(">>> 🛠️ Tool: 'get_all_unique_animals' called")
    unique_animal_names = set()
    for animal in ZOO_ANIMALS:
        unique_animal_names.add(animal["name"])
    return sorted(list(unique_animal_names))


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
