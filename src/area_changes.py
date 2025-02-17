import logging
import os

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, format_id
from util.logger import Logger


def parse_wild_pokemon(wild_pokemon: list[str], logger: Logger) -> str:
    """
    Parse the wild Pokémon data into markdown format.

    :param wild_pokemon: The wild Pokémon data to parse.
    :param logger: The logger object to use for logging.

    :return: The parsed wild Pokémon data in markdown format.
    """

    # Initialize markdown string
    wild_pokemon_md = ""

    # Parse wild Pokémon data
    for line in wild_pokemon:
        if line.startswith("Method"):
            continue
        elif line.startswith("Hint:") or line.startswith("Note:"):
            wild_pokemon_md += f"{line}\n\n"
            continue
        method, level, species = [s.strip() for s in line.split(" | ")]
        wild_pokemon = species.split(", ")

        wild_pokemon_md += f"{method} (Lv. {level})\n\n<pre><code>"
        for i, p in enumerate(wild_pokemon, 1):
            chance = "5" if p.endswith("*") else "10"
            wild_pokemon_md += f"{i}. <a href='/rrss-wiki/pokemon/{format_id(p)}/'>{p}</a> ({chance}%)\n"
        wild_pokemon_md += "</code></pre>\n\n"

    return wild_pokemon_md


def parse_changes(area_changes: dict, logger: Logger) -> tuple[str, str]:
    """
    Parse the area changes data into markdown format.

    :param area_changes: The area changes data to parse.
    :param logger: The logger object to use for logging.

    :return: The parsed area changes data in markdown format.
    """

    # Initialize markdown strings
    mds = {
        "wild_pokemon": "",
        "trainers": "",
    }

    # Parse area changes data
    for area, sections in area_changes.items():
        first_pass = True

        for section, categories in sections.items():
            logger.log(logging.DEBUG, f"Parsing area changes for {area} [ {section} ]...")

            for category, changes in categories.items():
                # Skip empty categories
                if len(changes) == 0:
                    continue

                # Add location headers
                if first_pass:
                    mds[category] += f"## {area}\n\n"
                    mds[category] += "" if section == "Main Area" or len(sections) == 1 else f"### [ {section} ]\n\n"
                else:
                    mds[category] += f"## {area}\n\n" if section == "Main Area" else f"### [ {section} ]\n\n"

                # Parse change data
                if category == "wild_pokemon":
                    mds[category] += parse_wild_pokemon(changes, logger)
                elif category == "trainers":
                    pass

            first_pass = False

    return mds["wild_pokemon"], mds["trainers"]


def main():
    """
    Main function for the area changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Area Changes Parser", LOG_PATH + "area_changes.log", LOG)

    # Read input data file
    file_path = INPUT_PATH + "AreaChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)

    mds = {
        "wild_pokemon": "# Wild Pokémon\n\n---\n\nOverview\n\n",
        "trainers": "# Trainer Pokémon\n\n---\n\nOverview\n\n",
    }
    area_changes = {}
    curr_location = None
    curr_section = None
    change_key = "wild_pokemon"
    postgame = False

    # Parse all lines from the input data file
    logger.log(logging.INFO, f"Parsing {n} lines of data from {file_path}...")
    i = 0
    while i < n:
        # Get line data
        line = lines[i]
        last_line = lines[i - 1] if i > 0 else None
        next_line = lines[i + 1] if i + 1 < n else None
        logger.log(logging.DEBUG, f"Parsing line {i + 1}/{n}: {line}")

        # Skip empty lines
        if check_empty(line):
            change_key = "wild_pokemon" if line == "" else change_key
        # Table lines
        elif line.startswith("| "):
            line = line.strip("| ")

            # Location header
            if last_line == "o----------------------o":
                line = line.strip(")")
                curr_location, curr_section = line.split(" (") if " (" in line else (line, "Main Area")
                if curr_location.endswith(curr_section):
                    curr_section = "Main Area"
                if postgame:
                    curr_section += " (Postgame)"

                area_changes[curr_location] = area_changes.get(curr_location, {})
                area_changes[curr_location][curr_section] = {"wild_pokemon": [], "trainers": []}
            # Change table formatting
            elif " | " in line:
                area_changes[curr_location][curr_section][change_key].append(line)
            # Overview table
            else:
                while i < n and not check_empty(next_line):
                    line += " " + next_line.strip("| ")
                    i += 1
                    next_line = lines[i + 1]

                if line.startswith("Trainers"):
                    change_key = "trainers"
                elif line == "POST GAME":
                    postgame = True
                elif curr_location in area_changes:
                    area_changes[curr_location][curr_section][change_key].append(line)
                else:
                    mds[change_key] += line + "\n\n"
        # Header lines
        elif line.startswith("#"):
            md = f"---\n\n{line}\n\n"
            mds["wild_pokemon"] += md
            mds["trainers"] += md
        # Miscellaneous lines
        else:
            md = line + "\n\n"
            mds["wild_pokemon"] += md
            mds["trainers"] += md

        # Move to the next line
        i += 1
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")

    # Parse area changes data
    wild_pokemon_md, trainers_md = parse_changes(area_changes, logger)
    mds["wild_pokemon"] += wild_pokemon_md
    mds["trainers"] += trainers_md

    # Save parsed data to output file
    save(OUTPUT_PATH + "wild_pokemon.md", mds["wild_pokemon"], logger)
    save(OUTPUT_PATH + "trainer_pokemon.md", mds["trainers"], logger)


if __name__ == "__main__":
    main()
