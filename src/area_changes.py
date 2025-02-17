import logging
import os

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty, find_pokemon_sprite, format_id, revert_id
from util.logger import Logger


def parse_wild_pokemon(area: str, section: str, wild_pokemon: list[str], logger: Logger) -> tuple[str, str]:
    """
    Parse the wild Pokémon data into markdown format.

    :param wild_pokemon: The wild Pokémon data to parse.
    :param logger: The logger object to use for logging.

    :return: The parsed wild Pokémon data in markdown format.
    """

    # Initialize markdown string
    wild_pokemon_md = ""
    section_md = ""

    # Parse wild Pokémon data
    for line in wild_pokemon:
        if line.startswith("Method"):
            continue
        elif line.startswith("Hint:") or line.startswith("Note:"):
            tip, text = line.split(": ")
            md = f"**{tip}:** <i>{text}</i>\n\n"
            wild_pokemon_md += md
            section_md += md
            continue

        method, level, species = [s.strip() for s in line.split(" | ")]
        wild_pokemon = species.split(", ")

        wild_pokemon_md += f"**{method}** (Lv. {level})\n\n<pre><code><ol>"
        section_md += f"### {method}\n\n"
        section_md += "| Sprite | Pokémon | Encounter Type | Level | Chance |\n"
        section_md += "|:------:|---------|:--------------:|-------|--------|\n"

        n = len(wild_pokemon)
        chance = str(100 // n)
        for p in wild_pokemon:
            if n > 9:
                chance = "5" if p.endswith("*") else "10"
            wild_pokemon_md += f"<li><a href='/rrss-wiki/pokemon/{format_id(p)}/'>{p}</a> ({chance}%)</li>"

            sprite = find_pokemon_sprite(p, "front", logger).replace("../", "../../")
            encounter_id = format_id(method, symbol="_")
            section_md += f"| {sprite} | [{p}](../../pokemon/{format_id(p)}.md/) | "
            section_md += f'![{method}](../../assets/encounter_types/{encounter_id}.png "{method}")<br>{method}'
            section_md += f" | {level} | {chance}% |\n"
        wild_pokemon_md += "</ol></code></pre>\n\n"
        section_md += "\n"

    return wild_pokemon_md, section_md


def parse_trainers(area: str, section: str, trainers: list[str], logger: Logger) -> tuple[str, str]:
    return "", ""


def parse_changes(area_changes: dict, dir_path: str, logger: Logger) -> tuple[str, str]:
    """
    Parse the area changes data into markdown format.

    :param area_changes: The area changes data to parse.
    :param logger: The logger object to use for logging.

    :return: The parsed area changes data in markdown format.
    """

    # Initialize markdown strings
    mds = {
        "wild_pokemon": "",
        "trainer_pokemon": "",
        "special_battles": "",
    }

    # Parse area changes data
    for area, sections in area_changes.items():
        first_pass = True
        area_mds = {
            "wild_pokemon": "",
            "trainer_pokemon": "",
            "special_battles": "",
        }

        for section, categories in sections.items():
            logger.log(logging.DEBUG, f"Parsing area changes for {area} [ {section} ]...")

            for category, changes in categories.items():
                # Skip empty categories
                if len(changes) == 0:
                    continue

                # Add location headers
                if first_pass:
                    mds[category] += f"## {area}\n\n"
                    area_mds[category] = f"# {area} — {revert_id(category, symbol='_')}\n\n"

                    section_md = "" if section == "Main Area" or len(sections) == 1 else f"### [ {section} ]\n\n"
                else:
                    section_md = f"## {area}\n\n" if section == "Main Area" else f"### [ {section} ]\n\n"
                mds[category] += section_md
                area_mds[category] += section_md.replace("###", "##")

                # Parse change data
                md, area_md = (
                    parse_wild_pokemon(area, section, changes, logger)
                    if category == "wild_pokemon"
                    else parse_trainers(area, section, changes, logger)
                )
                mds[category] += md
                area_mds[category] += area_md

            first_pass = False

        # Save area changes data to wild encounters
        area_id = format_id(area)
        for category in area_mds:
            if area_mds[category] != "":
                save(f"{dir_path}{area_id}/{category}.md", area_mds[category], logger)

    return mds["wild_pokemon"], mds["trainer_pokemon"]


def main():
    """
    Main function for the area changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")
    NAV_OUTPUT_PATH = os.getenv("NAV_OUTPUT_PATH")
    WILD_ENCOUNTER_PATH = os.getenv("WILD_ENCOUNTER_PATH")

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
        "wild_pokemon": "# Wild Pokémon\n\n---\n\n## Overview\n\n",
        "trainer_pokemon": "# Trainer Pokémon\n\n---\n\n## Overview\n\n",
        "special_battles": "# Special Battles\n\n",
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
                area_changes[curr_location][curr_section] = {
                    "wild_pokemon": [],
                    "trainer_pokemon": [],
                    "special_battles": [],
                }
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
                    change_key = "trainer_pokemon"
                elif line.startswith("Special Battle"):
                    change_key = "special_battles"
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
            mds["trainer_pokemon"] += md
        # Miscellaneous lines
        else:
            md = line + "\n\n"
            mds["wild_pokemon"] += md
            mds["trainer_pokemon"] += md

        # Move to the next line
        i += 1
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")

    # Parse area changes data
    wild_pokemon_md, trainers_md = parse_changes(area_changes, WILD_ENCOUNTER_PATH, logger)
    mds["wild_pokemon"] += wild_pokemon_md
    mds["trainer_pokemon"] += trainers_md

    # Generate wild encounter nav
    nav = ""
    for area in area_changes:
        area_id = format_id(area)
        nav += f"      - {area}:\n"

        has_keys = {
            "special_battles": "Special Battles",
            "trainer_pokemon": "Trainer Pokémon",
            "wild_pokemon": "Wild Pokémon",
        }
        for key in has_keys:
            has_key = next(
                (True for section in area_changes[area] if len(area_changes[area][section][key]) > 0), False
            )
            if has_key:
                nav += f"          - {has_keys[key]}: wild_encounters/{area_id}/{key}.md\n"
    save(NAV_OUTPUT_PATH + "wild_encounter_nav.yml", nav, logger)

    # Save parsed data to output file
    save(OUTPUT_PATH + "wild_pokemon.md", mds["wild_pokemon"], logger)
    save(OUTPUT_PATH + "trainer_pokemon.md", mds["trainer_pokemon"], logger)
    save(OUTPUT_PATH + "special_battles.md", mds["special_battles"], logger)


if __name__ == "__main__":
    main()
