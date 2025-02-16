import logging
import math
import os

from dotenv import load_dotenv

from util.data import Data
from util.file import load, save
from util.format import check_empty
from util.logger import Logger


def add_items(item_list: list[str], data_item: Data) -> str:
    """
    Add items to the markdown string.

    :param item_list: List of items to add to the markdown string
    :param data_item: Item data object
    :return: Markdown string with items
    """

    item_md = ""
    n = len(item_list)
    half = math.ceil(n / 2)

    # Add items to the markdown string
    item_md += (
        "<ol><li>"
        + "</li><li>".join([data_item.get_tooltip(item, "sun-moon") for item in item_list[:half]])
        + "</li></ol> | "
    )
    item_md += (
        f'<ol start="{half + 1}"><li>'
        + "</li><li>".join([data_item.get_tooltip(item, "sun-moon") for item in item_list[half:]])
        + "</li></ol> |\n"
    )

    # Clear the item list and return
    item_list.clear()
    return item_md


def main():
    """
    Main function for the item changes parser.

    :return: None
    """

    # Load environment variables
    load_dotenv()
    INPUT_PATH = os.getenv("INPUT_PATH")
    OUTPUT_PATH = os.getenv("OUTPUT_PATH")

    # Initialize logger object
    LOG = os.getenv("LOG") == "True"
    LOG_PATH = os.getenv("LOG_PATH")
    logger = Logger("Item Changes Parser", LOG_PATH + "item_changes.log", LOG)

    # Initialize item data object
    ITEM_INPUT_PATH = os.getenv("ITEM_INPUT_PATH")
    data_item = Data(ITEM_INPUT_PATH, logger)

    # Read input data file
    file_path = INPUT_PATH + "ItemChanges.txt"
    data = load(file_path, logger)
    lines = data.split("\n")
    n = len(lines)
    md = "# Item Changes\n\n---\n\n## Overview\n\n"

    parse_table = False
    item_list = []

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
                    md += f"| {line} |\n"
                    md += f"| {' | '.join(dividers)} |\n"
                    parse_table = True
                # Table item list
                elif columns[1].count(",") > 1:
                    items = columns[1].strip(",").split(",")
                    item_list.extend(items)
                    md += f"| {columns[0]} | "
                    if check_empty(next_line):
                        md += add_items(item_list, data_item)
                # Table body
                else:
                    # Add tooltips to item names
                    if len(columns) == 6:
                        columns[0] = data_item.get_tooltip(columns[0], "sun-moon")
                        columns[3] = data_item.get_tooltip(columns[3], "sun-moon")

                    # Add table row to markdown string
                    md += f"| {' | '.join(columns)} |\n"
                    if check_empty(next_line):
                        parse_table = False
                        md += "\n"
            # Overview table
            else:
                # Parse table paragraph
                while i < n and not check_empty(next_line):
                    line += " " + next_line.strip("| ")
                    i += 1
                    next_line = lines[i + 1]

                if line.count(",") - line.count(".") > 1:
                    # Table item list (cont.)
                    if parse_table:
                        items = line.split(",")
                        item_list.extend(items)
                        md += add_items(item_list, data_item)
                    # Item change list
                    else:
                        md += "\n".join(["1. " + data_item.get_tooltip(item, "sun-moon") for item in line.split(",")])
                        md += "\n"
                # Table paragraph
                else:
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
    save(OUTPUT_PATH + "item_changes.md", md, logger)


if __name__ == "__main__":
    main()
