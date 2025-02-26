import logging
import math
import os
import re

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty, find_pokemon_sprite, format_id
from util.logger import Logger

stat_ids = {
    "HP": "hp",
    "Attack": "attack",
    "Atk": "attack",
    "Defense": "defense",
    "Def": "defense",
    "Sp. Attack": "special-attack",
    "Sp. Atk": "special-attack",
    "Sp. Defense": "special-defense",
    "Sp. Def": "special-defense",
    "Speed": "speed",
    "Spd": "speed",
    "Total": "total",
}


def replace_move(move_changes: str, learn_method: str, data: dict, data_move: Data) -> None:
    move_str = ""

    for move in move_changes.split(", "):
        # Add the move to the move string
        move_str += f"{data_move.get_tooltip(move, 'omega-ruby-alpha-sapphire')}, "

        # Get Pokemon move list
        move_id = format_id(move)
        moves = data["moves"]["omega-ruby-alpha-sapphire"]
        move_index = next(
            (i for i, m in enumerate(moves) if m["name"] == move_id and m["learn_method"] == learn_method), None
        )

        # Add or replace the move in the data
        learn_data = {"name": move_id, "level_learned_at": 0, "learn_method": learn_method}
        if move_index is None:
            moves.append(learn_data)
        else:
            moves[move_index] = learn_data

    return move_str[:-2]


def change_attribute(
    attribute: str,
    change: str,
    pokemon: str,
    forms: list[str],
    data_pokemon: Data,
    data_item: Data,
    data_ability: Data,
    data_move: Data,
) -> str:
    attribute_change = f"**{attribute}**: {change}"

    for form in forms:
        data = data_pokemon.get_data(pokemon + form)

        # Pokemon location/obtainment method
        if attribute == "Location":
            data["locations"] = change.split(", ")
        # Pokemon held item changes
        elif attribute == "Held Item":
            attribute_change = f"**{attribute}**: "

            for item in change.split(", "):
                # Parse the item and chance
                item, chance = item.rsplit(" ", 1)
                item_id = format_id(item)
                chance_int = int(chance[1:-2])

                # Add the item to the attribute change string
                attribute_change += f"{data_item.get_tooltip(item, 'sun-moon')} {chance}, "

                # Add the held item to the data
                held_items = data["held_items"]
                held_items[item_id] = held_items.get(item_id, {})
                held_items[item_id]["omega-ruby"] = int(chance_int)
                held_items[item_id]["alpha-sapphire"] = int(chance_int)

            attribute_change = attribute_change[:-2]
        # Pokemon type changes
        elif attribute == "Type":
            old_type, new_type = change.split(" >> ")
            old_types = old_type.split("/")
            new_types = new_type.split("/")
            data["types"] = [format_id(t) for t in new_types]

            # Format the type change
            attribute_change = f"**{attribute}**: "
            attribute_change += " ".join([f"![{t}](../../assets/types/{format_id(t)}.png)" for t in old_types])
            attribute_change += " >> "
            attribute_change += " ".join([f"![{t}](../../assets/types/{format_id(t)}.png)" for t in new_types])
        # Pokemon EV yield changes
        elif attribute == "Effort Values":
            evs = change.split(" >> ")[1].split(", ")

            for ev in evs:
                num, stat = ev.split(" ", 1)
                stat = stat_ids[stat]
                data["ev_yield"][stat] = int(num)
        # Pokemon ability changes
        elif attribute == "Base Happiness":
            happiness = int(change.split(" >> ")[1])
            data["base_happiness"] = happiness
        # Pokemon capture rate changes
        elif attribute == "Catch Rate":
            catch_rate = int(change.split(" >> ")[1])
            data["capture_rate"] = catch_rate
        # Pokemon ability changes
        elif attribute.startswith("Ability"):
            slot = int(attribute[-1])
            asterisks = " " + change.rsplit(" ", 1)[1] if change.endswith("*") else ""
            change = change.strip(" *")
            old_ability, new_ability = change.split(" >> ") if " >> " in change else (None, change)

            # Format the ability change
            attribute_change = f"**{attribute}**: "
            new_tooltip = data_ability.get_tooltip(new_ability, "omega-ruby-alpha-sapphire")
            attribute_change += (
                f"{data_ability.get_tooltip(old_ability, 'omega-ruby-alpha-sapphire')} >> {new_tooltip}"
                if old_ability
                else f"{new_tooltip}"
            ) + asterisks

            # Ability data formatting
            ability_data = {
                "name": format_id(new_ability),
                "hidden": slot == 3,
                "slot": slot,
            }

            # Replace the ability or add it to the list
            abilities = data["abilities"]
            ability_index = next((i for i, a in enumerate(abilities) if a["slot"] == slot), None)
            if ability_index is not None:
                abilities[ability_index] = ability_data
            else:
                abilities.append(ability_data)
        # Pokemon move changes
        elif attribute == "New TM/HMs":
            attribute_change = f"**{attribute}**: " + replace_move(change, "machine", data, data_move)
        elif attribute == "Move Tutor":
            attribute_change = f"**{attribute}**: " + replace_move(change, "tutor", data, data_move)
        # Skip evolution (parsed from seperate file)
        elif attribute.startswith("Evolution"):
            pass

    return attribute_change + "\n\n"


def change_table(changes: list[str], pokemon: str, forms: list[str], data_pokemon: Data, data_move: Data) -> str:
    table = ""

    ## Stat changes
    if " >> " in changes[-1]:
        table += "**Base Stat Changes:**\n\n"
        table += "| Stat | Base | Change |\n"
        table += "| ---- | ---- | ------ |\n"

        # Stat formatting constants
        pattern = r"([A-Z. a-z]+)([0-9]+) >> ([0-9]+)"

        for form in forms:
            data = data_pokemon.get_data(pokemon + form)
            for change in changes:
                # Format the stat data
                stat, base, change = re.match(pattern, change).groups()
                stat = stat.strip()
                stat_id = stat_ids[stat]

                # Add the stat to the table and the data
                table += f"| {stat} | {base} | {change} |\n"
                data["stats"][stat_id] = int(change)

            data_pokemon.save_data(pokemon + form, data)
    # Level up move changes
    else:
        table += "**Level Up Moves:**\n\n"
        table += "| Moves | Level |     | Cont. | Level |\n"
        table += "| ----- | ----- | --- | ----- | ----- |\n"

        # Parse the move data
        pattern = r"([0-9]+) ([A-Z' \-a-z]+)"
        n = len(changes)
        half = math.ceil(n / 2)

        for form in forms:
            data = data_pokemon.get_data(pokemon + form)

            # Remove all level-up moves
            data["moves"]["omega-ruby-alpha-sapphire"] = [
                move for move in data["moves"]["omega-ruby-alpha-sapphire"] if move["learn_method"] != "level-up"
            ]
            moves = data["moves"]["omega-ruby-alpha-sapphire"]

            for i in range(half):
                for j in range(2):
                    # Get the move index
                    index = i + j * half
                    if index >= n:
                        table += "|   |   |   "
                        break

                    # Format the move data
                    move = changes[index]
                    level, move = re.match(pattern, move).groups()

                    # Add the move to the table and the data
                    table += f"| {data_move.get_tooltip(move, 'omega-ruby-alpha-sapphire')} | {level} |   "
                    moves.append({"name": format_id(move), "level_learned_at": int(level), "learn_method": "level-up"})
                table = table[:-3] + "\n"

            data_pokemon.save_data(pokemon + form, data)

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

    # Initialize data objects
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")
    data_pokemon = Data(POKEMON_INPUT_PATH, logger)
    MOVE_INPUT_PATH = os.getenv("MOVE_INPUT_PATH")
    data_move = Data(MOVE_INPUT_PATH, logger)
    ITEM_INPUT_PATH = os.getenv("ITEM_INPUT_PATH")
    data_item = Data(ITEM_INPUT_PATH, logger)
    ABILITY_INPUT_PATH = os.getenv("ABILITY_INPUT_PATH")
    data_ability = Data(ABILITY_INPUT_PATH, logger)

    # Read input data file
    file_path = INPUT_PATH + "PokemonChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Overview\n\n---\n\n"

    changes = []
    curr_pokemon = None
    curr_forms = [""]

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
                md += change_table(changes, curr_pokemon, curr_forms, data_pokemon, data_move)
                md += "\n"
        # Table lines
        elif line.startswith("| "):
            line = line.strip("| ")

            while i < n and not check_empty(next_line):
                line += ("\n" if next_line[3] == "." else " ") + next_line.strip("| ")
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
                curr_form = "-" + form.split(" ")[0].lower()

                if curr_form == "-normal":
                    forms.append(f"[{curr_pokemon}](../../pokemon/{format_id(curr_pokemon)}.md/)")
                else:
                    pokemon_id = curr_pokemon + curr_form
                    forms.append(f"[{form}](../../pokemon/{format_id(pokemon_id)}.md/)")
                    sprites.append(
                        find_pokemon_sprite(pokemon_id, "front", data_pokemon, logger).replace("../", "../../")
                    )
                    curr_forms.append(curr_form)

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
            curr_forms = [""]
            sprite = find_pokemon_sprite(curr_pokemon, "front", data_pokemon, logger).replace("../", "../../")

            md += f"---\n\n## [{num} {curr_pokemon}](../../pokemon/{format_id(curr_pokemon)}.md/)\n\n"
            md += sprite + "\n\n"
        # Pokemon attribute changes
        elif ": " in line:
            attribute, change = line.split(": ")
            md += change_attribute(
                attribute, change, curr_pokemon, curr_forms, data_pokemon, data_item, data_ability, data_move
            )
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
