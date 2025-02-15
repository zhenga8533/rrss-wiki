import logging
import math
import os
import re

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty, find_pokemon_sprite
from util.logger import Logger


def change_attribute(attribute: str, change: str, logger: Logger) -> str:
    pass


def change_table(changes: list[str], pokemon: str, pokemon_data: Data, logger: Logger) -> str:
    table = ""
    data = pokemon_data.get_data(pokemon)

    if " >> " in changes[-1]:
        table += "| Stat | Base | Change |\n"
        table += "| ---- | ---- | ------ |\n"

        pattern = r"([A-Z. a-z]+)([0-9]+) >> ([0-9]+)"
        stat_ids = {
            "HP": "hp",
            "Attack": "attack",
            "Defense": "defense",
            "Sp. Attack": "special-attack",
            "Sp. Defense": "special-defense",
            "Speed": "speed",
            "Total": "total",
        }

        for change in changes:
            stat, base, change = re.match(pattern, change).groups()
            stat = stat.strip()
            stat_id = stat_ids[stat]

            table += f"| {stat} | {base} | {change} |\n"
            data["stats"][stat_id] = int(change)
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

    pokemon_data.save_data(pokemon, data)
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

    # Initialize item data object
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")
    pokemon_data = Data(POKEMON_INPUT_PATH, logger)

    # Read input data file
    file_path = INPUT_PATH + "PokemonChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Overview\n\n---\n\n"

    changes = []
    curr_pokemon = None
    curr_form = ""

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
                md += change_table(changes, curr_pokemon + curr_form, pokemon_data, logger)
                md += "\n"
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
        elif line.endswith("Forme"):
            forms = []
            sprites = []

            # Get all forms of the current Pokemon
            for form in line.split(", "):
                forms.append(form)
                curr_form = "-" + form.split(" ")[0].lower()

                if curr_form != "-normal":
                    pokemon_id = curr_pokemon + curr_form
                    sprites.append(find_pokemon_sprite(pokemon_id, "front", logger).replace("../", "../../"))
                else:
                    curr_form = ""

            # Add the forms to the markdown file
            md += f"### {', '.join(forms)}\n\n"
            md += " ".join(sprites) + "\n\n"
        # Pokemon headers
        elif next_line.startswith("==="):
            # Save the changes to the appropriate region file
            num, curr_pokemon = line.split(" ", 1)
            index = int(num[1:])
            md = save_region(index, md, OUTPUT_PATH, logger)

            # Add Pokemon header to the markdown file
            curr_pokemon = curr_pokemon.title()
            curr_form = ""
            sprite = find_pokemon_sprite(curr_pokemon, "front", logger).replace("../", "../../")

            md += f"---\n\n## {num} {curr_pokemon}\n\n"
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
