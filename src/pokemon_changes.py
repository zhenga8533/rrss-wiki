import logging
import math
import os
import re

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, find_pokemon_sprite
from util.logger import Logger


def change_attribute(attribute: str, change: str, logger: Logger) -> str:
    pass


def change_table(changes: list[str], logger: Logger) -> str:
    table = ""

    if " >> " in changes[-1]:
        table += "| Stat | Base | Change |\n"
        table += "| ---- | ---- | ------ |\n"

        pattern = r"([A-Z. a-z]+) ([0-9]+) >> ([0-9]+)"
        for change in changes:
            stat, base, change = re.match(pattern, change).groups()
            table += f"| {stat} | {base} | {change} |\n"
    else:
        table += "| Level | Move | Cont. | Move |\n"
        table += "| ----- | ---- | ----- | ---- |\n"

        pattern = r"([0-9]+) ([A-Z a-z]+)"
        n = len(changes)
        half = math.ceil(n / 2)

        for i in range(half):
            move1 = changes[i]
            level1, move1 = re.match(pattern, move1.strip(" *")).groups()
            table += f"| {level1} | {move1} |"

            if i + half < n:
                move2 = changes[i + half]
                level2, move2 = re.match(pattern, move2.strip(" *")).groups()
                table += f" {level2} | {move2} |\n"
            else:
                table += " | |\n"

    changes.clear()
    return table


def main():
    """
    Main function for the pokemon changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Pokémon Changes Parser", LOG_PATH + "pokemon_changes.log", LOG)

    # Read input data file
    file_path = INPUT_PATH + "PokemonChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Pokémon Changes\n\n---\n\n## Overview\n\n"

    changes = []
    parse_table = False

    # Parse all lines from the input data file
    logger.log(logging.INFO, f"Parsing {n} lines of data from {file_path}...")
    i = 0
    while i < n:
        # Get line data
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < n else ""
        logger.log(logging.DEBUG, f"Parsing line {i + 1}/{n}: {line}")

        # Skip empty lines
        if check_empty(line):
            if len(changes) > 0:
                md += change_table(changes, logger) + "\n"
                parse_table = False
        # Table lines
        elif line.startswith("| "):
            line = line.strip("| ")

            while i < n and not check_empty(next_line):
                line += " " + next_line.strip("| ")
                i += 1
                next_line = lines[i + 1]

            if line.startswith("- "):
                md += "\t"
            md += line + "\n\n"
        # Pokemon headers
        elif line.endswith("Forme"):
            pass
        elif next_line.startswith("==="):
            num, pokemon = line.split(" ", 1)
            pokemon = pokemon.title()
            sprite = find_pokemon_sprite(pokemon, "front", logger)

            md += f"<h3>{num} {pokemon}</h3>\n\n"
            md += sprite + "\n\n"
            parse_table = True
        elif ": " in line:
            attribute, change = line.split(": ")
            md += f"**{attribute}:** {change}\n\n"
        # Header lines
        elif line.startswith("#"):
            md += f"---\n\n{line}\n\n"
        elif parse_table:
            changes.append(line)
        # Miscellaneous lines
        else:
            md += line + "\n\n"

        # Move to the next line
        i += 1
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")

    # Save parsed data to output file
    save(OUTPUT_PATH + "pokemon_changes.md", md, logger)


if __name__ == "__main__":
    main()
