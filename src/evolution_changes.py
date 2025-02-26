import logging
import os

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty, find_pokemon_sprite, format_id
from util.logger import Logger


def change_evolution(evolutions: list[dict], pokemon: str, change: str, logger: Logger) -> list:
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
        pokemon_evolutions += change_evolution(evolution.get("evolutions", []), pokemon, change, logger)

    return pokemon_evolutions


def change_pokemon(columns: list[str], data_pokemon: Data, logger: Logger) -> None:
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
    data = data_pokemon.get_data(id)
    evolutions = data["evolutions"]

    # Change evolution data and save changes
    pokemon_evolutions = change_evolution(evolutions, id, evolution_method, logger)
    for pokemon in pokemon_evolutions:
        evolution_data = data_pokemon.get_data(pokemon)
        evolution_data["evolutions"] = evolutions
        data_pokemon.save_data(pokemon, evolution_data)


def main():
    """
    Main function for the evolution changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Evolution Changes Parser", LOG_PATH + "evolution_changes.log", LOG)

    # Initialize Pokemon data object
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")
    data_pokemon = Data(POKEMON_INPUT_PATH, logger)

    # Read input data file
    file_path = INPUT_PATH + "EvolutionChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Evolution Changes\n\n---\n\n## Overview\n\n"

    parse_table = False

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
                columns = [s.strip() for s in line.split(" | ")]

                # Table header
                if not parse_table:
                    dividers = ["---"] * len(columns)
                    dividers[1] = ":---:"
                    dividers[2] = ":---:"

                    md += f"| {line} |\n"
                    md += f"| {' | '.join(dividers)} |\n"
                    parse_table = True
                # Table body (evolution changes)
                else:
                    change_pokemon(columns, data_pokemon, logger)
                    pre = columns[1]
                    evo = columns[2]

                    columns[1] = (
                        f'<div class="sprite-cell">{find_pokemon_sprite(pre, "front", data_pokemon, logger)}<br>[{pre}](../pokemon/{format_id(pre)}.md/)</div>'
                    )
                    columns[2] = (
                        f'<div class="sprite-cell">{find_pokemon_sprite(evo, "front", data_pokemon, logger)}<br>[{evo}](../pokemon/{format_id(evo)}.md/)</div>'
                    )
                    md += f"| {' | '.join(columns) } |\n"

                    # Add new line to bottom of table
                    if check_empty(next_line):
                        parse_table = False
                        md += "\n"
            # Overview table
            else:
                while i < n and not check_empty(next_line):
                    line += " " + next_line.strip("| ")
                    i += 1
                    next_line = lines[i + 1]

                if line.startswith("- "):
                    md += "\t"
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
