import logging
import os

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, find_pokemon_sprite
from util.logger import Logger


def main():
    """
    Main function for the encounter changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Encounter Changes Parser", LOG_PATH + "encounter_changes.log", LOG)

    # Read input data file
    file_path = INPUT_PATH + "EncounterChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Encounter Changes\n\n---\n\n## Overview\n\n"

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
                    dividers = ["---"] * (len(columns) + 1)
                    dividers[0] = ":---:"

                    md += f"| Pokémon | {line} |\n"
                    md += f"| {' | '.join(dividers)} |\n"
                    parse_table = True
                # Table body (Encounter changes)
                else:
                    description, pokemon = columns[0].split(", ")
                    sprite = find_pokemon_sprite(pokemon, "front", logger)
                    columns = (
                        [pokemon, description, *columns[1:]]
                        if sprite == "?"
                        else [
                            f"<div class='sprite-cell'>{sprite}<br>{pokemon}</div>",
                            description,
                            "<br>".join(
                                [f"{i}. {change.capitalize()}" for i, change in enumerate(columns[1].split(", "), 1)]
                            ),
                        ]
                    )

                    md += f"| {' | '.join(columns) } |\n"

                    # Add new line to bottom of table
                    if check_empty(next_line):
                        parse_table = False
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
    save(OUTPUT_PATH + "encounter_changes.md", md, logger)


if __name__ == "__main__":
    main()
