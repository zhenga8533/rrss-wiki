import json
import logging
import os

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, format_id
from util.logger import Logger


def change_evolution(evolutions: list[dict], pokemon: str, change: str, pokemon_path: str, logger: Logger) -> list:
    pokemon_evolutions = []

    for evolution in evolutions:
        # Get evolution name
        name = evolution["name"]
        pokemon_evolutions.append(name)

        # Add evolution change to Pokemon data
        if name == pokemon:
            if evolution.get("evolution_changes") is None:
                evolution["evolution_changes"] = [change]
            elif change not in evolution["evolution_changes"]:
                evolution["evolution_changes"].append(change)

        # Recursively change evolution data
        pokemon_evolutions += change_evolution(evolution.get("evolutions", []), pokemon, change, pokemon_path, logger)

    return pokemon_evolutions


def change_pokemon(columns: list[str], pokemon_path: str, logger: Logger) -> None:
    # Parse evolution data
    unevolved = columns[1]
    evolved = columns[2]
    evolution_method = (
        f"{unevolved} now evolves into {evolved} via: {columns[3]}"
        if len(columns) < 6
        else f"{unevolved} now evolves into {evolved} at {columns[4]}."
    )

    # Load Pokemon data
    id = format_id(unevolved)
    data = json.loads(load(pokemon_path + id + ".json", logger))
    evolutions = data["evolutions"]

    # Change evolution data and save changes
    pokemon_evolutions = change_evolution(evolutions, id, evolution_method, pokemon_path, logger)
    for pokemon in pokemon_evolutions:
        evolution_data = json.loads(load(pokemon_path + format_id(pokemon) + ".json", logger))
        evolution_data["evolutions"] = evolutions
        save(pokemon_path + format_id(pokemon) + ".json", json.dumps(data, indent=4), logger)


def main():
    """
    Main function for the evolution changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Evolution Changes Parser", LOG_PATH + "evolution_changes.log", LOG)

    # Read input data file
    file_path = INPUT_PATH + "EvolutionChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Evolution Changes\n\n---\n\n## Overview\n\n"

    # Parse all lines from the input data file
    logger.log(logging.INFO, f"Parsing {n} lines of data from {file_path}...")
    i = 0
    while i < n:
        # Get line data
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < n else None
        logger.log(logging.DEBUG, f"Parsing line {i + 1}/{n}: {line}")

        # Skip empty lines
        if check_empty(line):
            pass
        # Table lines
        elif line.startswith("| "):
            line = line.strip("| ")

            # Change table formatting
            if " | " in line:
                md += f"| {line} |\n"
                columns = [s.strip() for s in line.split(" | ")]

                # Table header
                if line.startswith("###"):
                    dividers = " | ".join(["---"] * (len(columns) + 1))
                    md += f"| {dividers} |\n"
                # Table body (evolution changes)
                else:
                    change_pokemon(columns, POKEMON_INPUT_PATH, logger)

                # Add new line to bottom of table
                if check_empty(next_line):
                    md += "\n"
            # Overview table
            else:
                if line.startswith("- "):
                    md += "\t"
                while i < n and not check_empty(next_line):
                    line += " " + next_line.strip("| ")
                    i += 1
                    next_line = lines[i + 1]
                md += line + "\n\n"
        # Header lines
        elif line.startswith("#"):
            md += f"---\n\n{line}\n\n"
        # Miscellaneous lines
        else:
            md += line + "\n\n"

        # Move to the next line
        i += 1
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")

    # Save parsed data to output file
    save(OUTPUT_PATH + "evolution_changes.md", md, logger)


if __name__ == "__main__":
    main()
