import logging
import os
import re

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty, format_id
from util.logger import Logger


def change_move(move: str, changes: list[tuple[str, str, str]], data_move: Data, logger: Logger) -> None:
    """
    Change the attributes of a move based on the given changes.

    :param move: The name of the move to change.
    :param changes: The list of changes to apply to the move.
    :param data_move: The move data object to load and save move data.
    :param logger: The logger object to log messages to.
    :return: None
    """

    # Load move data
    move_data = data_move.get_data(move)

    # Loop through all changes
    for change in changes:
        attribute, old_value, new_value = change

        if attribute == "Power":
            move_data["power"] = int(new_value)
        elif attribute == "PP":
            move_data["pp"] = int(new_value)
        elif attribute == "Type":
            move_data["type"] = format_id(new_value)
        elif attribute == "Accuracy":
            move_data["accuracy"] = int(new_value)
        elif attribute == "Effect":
            effect_change = f" This move has a {new_value}."

            # Update effect
            if effect_change not in move_data["effect"]:
                move_data["effect"] += effect_change

            # Update ORAS flavor text
            flavor_text_entries = move_data["flavor_text_entries"]
            if effect_change not in flavor_text_entries["omega-ruby-alpha-sapphire"]:
                flavor_text_entries["omega-ruby-alpha-sapphire"] += effect_change
        elif "%" in attribute:
            if "Effect" in move_data:
                move_data["effect_chance"] = int(new_value)
            move_data["effect"] = move_data["effect"].replace(old_value, new_value)
        else:
            logger.log(logging.WARNING, f"Unknown attribute: {attribute}")

    # Save changes to move file
    data_move.save_data(move, move_data)


def main():
    """
    Main function for the attack changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Attack Changes Parser", LOG_PATH + "attack_changes.log", LOG)

    # Initialize move data object
    MOVE_INPUT_PATH = os.getenv("MOVE_INPUT_PATH")
    data_move = Data(MOVE_INPUT_PATH, logger)

    # Read input data file
    file_path = INPUT_PATH + "AttackChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Attack Changes\n\n---\n\n## Overview\n\n"

    # Parse all lines from the input data file
    logger.log(logging.INFO, f"Parsing {n} lines of data from {file_path}...")
    i = 0
    while i < n:
        # Get current line
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < n else None
        logger.log(logging.DEBUG, f"Parsing line {i + 1}/{n}: {line}")

        # Skip empty lines
        if check_empty(line):
            pass
        # Table lines
        elif line.startswith("| "):
            line = line.strip("| ")
            while i < n and not check_empty(next_line):
                line += " " + next_line.strip("| ")
                i += 1
                next_line = lines[i + 1]
            md += line + "\n\n"
        # Header lines
        elif line.startswith("#"):
            md += f"---\n\n{line}\n\n"
        # Move changes
        elif next_line.startswith("==="):
            # Line and table headers
            md += f"### {data_move.get_tooltip(line, 'omega-ruby-alpha-sapphire')}\n\n"
            md += "| Attribute | Old | New |\n"
            md += "| --------- | --- | --- |\n"

            # Parse move changes
            move = line
            changes = []
            i += 2

            while i < n and not check_empty(line := lines[i]):
                attribute, change = re.split(r"\s{2,}", line, 1)
                old, new = change.split(" >> ") if " >> " in change else ("None", change)
                md += f"| {attribute} | {old} | {new} |\n"

                changes.append((attribute, old, new))
                i += 1
            md += "\n"

            # Apply changes to move
            change_move(move, changes, data_move, logger)
        # Miscellaneous lines
        else:
            md += line + "\n\n"

        # Move to the next line
        i += 1
    logger.log(logging.INFO, f"Succesfully parsed {n} lines of data from {file_path}")

    # Save parsed data to output file
    save(OUTPUT_PATH + "attack_changes.md", md, logger)


if __name__ == "__main__":
    main()
