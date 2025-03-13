import logging
import os

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty, find_pokemon_sprite, find_trainer_sprite, format_id, revert_id
from util.logger import Logger


def parse_wild_pokemon(wild_pokemon: list[str], data_pokemon: Data, logger: Logger) -> tuple[str, str]:
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
        section_md += "| Sprite | Pokémon | Encounter | Chance |\n"
        section_md += "|:------:|---------|:---------:|--------|\n"

        n = len(wild_pokemon)
        chance = str(100 // n)
        for p in wild_pokemon:
            if n > 9:
                chance = "5" if p.endswith("*") else "10"
            wild_pokemon_md += f"<li><a href='/rrss-wiki/pokemon/{format_id(p)}/'>{p}</a> ({chance}%)</li>"

            sprite = find_pokemon_sprite(p, "front", data_pokemon, logger).replace("../", "../../")
            encounter_id = format_id(method, symbol="_")
            section_md += f"| {sprite} | [{p}](../../pokemon/{format_id(p)}.md/)<br>Lv. {level} | "
            section_md += f'![{method}](../../assets/encounter_types/{encounter_id}.png "{method}")<br>{method}'
            section_md += f" | {chance}% |\n"
        wild_pokemon_md += "</ol></code></pre>\n\n"
        section_md += "\n"

    return wild_pokemon_md, section_md


def parse_trainers(trainers: list[str], data_pokemon: Data, logger: Logger) -> tuple[str, str]:
    # Initialize markdown string
    trainers_md = "<h3>Trainer Rosters</h3>\n\n"
    section_md = "### Trainer Rosters\n\n"
    section_table = ""

    def add_table_header(num):
        table_header = "| Trainer | " + " | ".join([f"P{i}" for i in range(1, num + 1)]) + " |\n"
        table_header += "|:-------:|" + (":--:|" * num) + "\n"
        return table_header

    # Parse trainer data
    num_pokemon = 0
    special_battle = False
    for line in trainers:
        if line.startswith("ID"):
            continue
        elif line == "Rematches":
            if section_table:
                section_md += add_table_header(num_pokemon) + section_table + "\n"
                section_table = ""

            trainers_md += "<h3>Rematches</h3>\n\n"
            section_md += "### Rematches\n\n"
            continue
        elif line.startswith("Special Battle"):
            if not special_battle:
                special_battle = True
                trainers_md += "<h3>Special Battles</h3>\n\n"

                section_md += add_table_header(num_pokemon) + section_table + "\n"
                section_md += "### Special Battles\n\n"
                section_table = ""

            trainer = line.split(" - ")[1]
            if line.startswith("Rival"):
                trainer = "Rival"
            trainers_md += f"1. {trainer}\n\n"
            section_md += f"1. [{trainer}]()\n\n"  # TODO: Add special battle links

            continue

        trainer_id, trainer, roster = [s.strip() for s in line.split("|")]

        trainers_md += f"1. {trainer} [{trainer_id}]\n\n"

        trainer_sprite = find_trainer_sprite(trainer, "trainers", logger).replace("../", "../../")
        section_table += f"| {trainer_sprite}<br>{trainer} [{trainer_id}] |"

        pokemon = roster.split(", ")
        num_pokemon = max(num_pokemon, len(pokemon))
        for i, p in enumerate(pokemon):
            p, level = p.rsplit(" ", 1)
            trainers_md += f"\t{i}. Lv. {level} [{p}](../pokemon/{format_id(p)}.md/)\n\n"

            pokemon_sprite = find_pokemon_sprite(p, "front", data_pokemon, logger).replace("../", "../../")
            pokemon_link = f"[{p}](../../pokemon/{format_id(p)}.md)"
            section_table += f' <div class="sprite-cell">{pokemon_sprite}<br>{pokemon_link}<br>Lv. {level}</div> |'
        section_table += "\n"

    if section_table:
        section_md += add_table_header(num_pokemon) + section_table + "\n"

    return trainers_md, section_md


def parse_special(trainers: list[str], data_pokemon: Data, logger: Logger) -> tuple[str, str]:
    # Initialize markdown string
    wild_pokemon_md = ""
    section_md = ""

    trainer = ""
    extension = ""

    # Parse special battles data
    for line in trainers:
        if line.startswith("Special Battle - "):
            if trainer != "":
                wild_pokemon_md = wild_pokemon_md[:-4] + "</code></pre>\n\n"

            trainer = line.split(" - ")[1]
            if trainer.startswith("Rival"):
                starter = trainer.rsplit(" ", 1)[1][1:-1]
                if starter == "Treecko":
                    wild_pokemon_md += "### Rival\n\n"
                    brendan_sprite = find_trainer_sprite("Brendan", "important_trainers", logger)
                    may_sprite = find_trainer_sprite("May", "important_trainers", logger)
                    wild_pokemon_md += f"{brendan_sprite} {may_sprite}\n\n"

                wild_pokemon_md += f'=== "{starter}"\n\n\t<pre><code>'
                extension = "\t"
            else:
                trainer_sprite = find_trainer_sprite(trainer, "important_trainers", logger)
                wild_pokemon_md += f"### {trainer}\n\n{trainer_sprite}\n\n<pre><code>"

                extension = ""
            continue
        elif line.startswith("Pokemon"):
            continue

        pokemon, level, item, ability, moves = [s.strip() for s in line.split(" | ")]

        wild_pokemon_md += (extension if not wild_pokemon_md.endswith(">") else "") + f"{pokemon} @ {item}\n"
        wild_pokemon_md += extension + f"<b>Ability:</b> {ability}\n"
        wild_pokemon_md += extension + f"<b>Level:</b> {level}\n"
        wild_pokemon_md += extension + "<b>Moves:</b>\n"
        wild_pokemon_md += (
            "\n".join([f"{extension}{i}. {m}" for i, m in enumerate(moves.split(", "), 1)]) + f"\n{extension}<br>"
        )

    wild_pokemon_md = wild_pokemon_md[:-4] + "</code></pre>\n\n"

    return wild_pokemon_md, section_md


def parse_changes(
    area_changes: dict, data_pokemon: Data, dir_path: str, keys: list[str], logger: Logger
) -> dict[str, str]:
    # Initialize markdown strings
    mds = {key: "" for key in keys}

    # Parse area changes data
    for area, sections in area_changes.items():
        first_pass = {key: True for key in keys}
        area_mds = {key: "" for key in keys}

        for section, categories in sections.items():
            logger.log(logging.DEBUG, f"Parsing area changes for {area} [ {section} ]...")

            for category, changes in categories.items():
                # Skip empty categories
                if len(changes) == 0:
                    continue

                # Add location headers
                if first_pass[category]:
                    mds[category] += f"---\n\n## {area}\n\n"
                    cat_changes = len([s for s in sections if len(sections[s][category]) > 0])
                    mds[category] += (
                        ""
                        if (section == "Main Area" and cat_changes == 1) or category == "special_battles"
                        else f"### [ {section} ]\n\n"
                    )

                    area_mds[category] = f"# {area} — {revert_id(category, symbol='_')}\n\n"
                    area_mds[category] += f"---\n\n## [ {section} ]\n\n"
                    first_pass[category] = False
                else:
                    mds[category] += f"### [ {section} ]\n\n" if category != "special_battles" else ""
                    area_mds[category] += f"---\n\n## [ {section} ]\n\n"

                # Parse change data
                md, area_md = (
                    parse_wild_pokemon(changes, data_pokemon, logger)
                    if category == "wild_pokemon"
                    else (
                        parse_trainers(changes, data_pokemon, logger)
                        if category == "trainer_pokemon"
                        else parse_special(changes, data_pokemon, logger)
                    )
                )
                mds[category] += md
                area_mds[category] += area_md

        # Save area changes data to wild encounters
        area_id = format_id(area)
        for category in area_mds:
            if area_mds[category] != "":
                save(f"{dir_path}{area_id}/{category}.md", area_mds[category], logger)

    return mds


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

    # Initialize Pokemon data object
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")
    data_pokemon = Data(POKEMON_INPUT_PATH, logger)

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
    keys = list(mds.keys())

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
                area_changes[curr_location][curr_section] = {key: [] for key in keys}
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
                    if " - " in line:
                        curr_section = line.split(" - ")[1]
                        location_changes = area_changes[curr_location]
                        if curr_section not in location_changes:
                            location_changes[curr_section] = {key: [] for key in keys}
                elif line.startswith("Special Battle"):
                    change_key = "special_battles"
                    section_changes = area_changes[curr_location][curr_section]
                    section_changes[change_key].append(line)
                    section_changes["trainer_pokemon"].append(line)
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
    change_mds = parse_changes(area_changes, data_pokemon, WILD_ENCOUNTER_PATH, keys, logger)
    for key in change_mds:
        mds[key] += change_mds[key]

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
