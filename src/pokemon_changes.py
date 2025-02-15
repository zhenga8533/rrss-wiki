import logging
import math
import os
import re

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, find_pokemon_sprite, format_id
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
        table += "| Level | Move |     | Cont. | Move |\n"
        table += "| ----- | ---- | --- | ----- | ---- |\n"

        pattern = r"([0-9]+) ([A-Z a-z]+)"
        n = len(changes)
        half = math.ceil(n / 2)

        for i in range(half):
            move1 = changes[i]
            level1, move1 = re.match(pattern, move1.strip(" *")).groups()
            table += f"| {level1} | {move1} |   | "

            if i + half < n:
                move2 = changes[i + half]
                level2, move2 = re.match(pattern, move2.strip(" *")).groups()
                table += f"{level2} | {move2} |\n"
            else:
                table += "  |   |\n"

    changes.clear()
    return table


def save_region(num: int, md: str, output_path: str, logger) -> str:
    """
    Save the current markdown data to the appropriate region file.

    :param num: The Pokedex number of the current Pokemon.
    :param md: The current markdown data.
    :param output_path: The path to the output directory.
    :param logger: The logger object.
    :return: An empty string if the data was saved, the markdown data otherwise.
    """

    regions = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos"]
    pokedex_index = [152, 252, 387, 494, 650, 722]

    if num in pokedex_index:
        region = regions[pokedex_index.index(num)]
        md = f"# {region} Pokémon\n\n" + md
        save(f"{output_path}pokemon_changes/{region.lower()}.md", md, logger)
        return ""

    return md


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
    md = "# Overview\n\n---\n\n"

    changes = []
    curr_pokemon = None

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
        # Pokemon forms
        elif line.endswith("Forme") or line.endswith("Cloak"):
            forms = []
            sprites = []

            # Get all forms of the current Pokemon
            for form in line.split(", "):
                forms.append(form)
                form = form.split(" ")[0].lower()

                if form != "normal":
                    pokemon_id = f"{curr_pokemon}-{form}"
                    sprites.append(find_pokemon_sprite(pokemon_id, "front", logger).replace("../", "../../"))

            # Add the forms to the markdown file
            md += f"### {', '.join(forms)}\n\n"
            md += " ".join(sprites) + "\n\n"
        # Pokemon headers
        elif next_line.startswith("==="):
            # Save the changes to the appropriate region file
            num, pokemon = line.split(" ", 1)
            index = int(num[1:])
            md = save_region(index, md, OUTPUT_PATH, logger)

            # Add Pokemon header to the markdown file
            pokemon = pokemon.title()
            curr_pokemon = format_id(pokemon)
            sprite = find_pokemon_sprite(pokemon, "front", logger).replace("../", "../../")

            md += f"---\n\n## {num} {pokemon}\n\n"
            md += sprite + "\n\n"
        # Pokemon attribute changes
        elif ": " in line:
            attribute, change = line.split(": ")
            md += f"**{attribute}:** {change}\n\n"
        # Header lines
        elif line == "## Changes":
            save(OUTPUT_PATH + "pokemon_changes/overview.md", md, logger)
            md = ""
        elif line.startswith("#"):
            md += f"---\n\n{line}\n\n"
        # Miscellaneous lines
        else:
            changes.append(line)

        # Move to the next line
        i += 1
    save_region(722, md, OUTPUT_PATH, logger)
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")


if __name__ == "__main__":
    main()
