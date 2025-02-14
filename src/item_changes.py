import logging
import math
import os

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty
from util.logger import Logger


def add_items(item_list: list[str]) -> str:
    """
    Add items to the markdown string.

    :param item_list: List of items to add to the markdown string
    :return: Markdown string with items
    """

    item_md = ""
    n = len(item_list)
    half = math.ceil(n / 2)

    # Add items to the markdown string
    item_md += "<br>".join([f"{i}. {item.strip()}" for i, item in enumerate(item_list[:half], 1)]) + " | "
    item_md += "<br>".join([f"{i}. {item.strip()}" for i, item in enumerate(item_list[half:], half + 1)]) + " |\n"

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
                        md += add_items(item_list)
                # Table body
                else:
                    md += f"| {line} |\n"
                    if check_empty(next_line):
                        parse_table = False
                        md += "\n"
            # Overview table
            else:
                # Parse table paragraph
                if line.startswith("- "):
                    md += "\t"
                while i < n and not check_empty(next_line):
                    line += " " + next_line.strip("| ")
                    i += 1
                    next_line = lines[i + 1]

                if line.count(",") - line.count(".") > 1:
                    # Table item list (cont.)
                    if parse_table:
                        items = line.split(",")
                        item_list.extend(items)
                        md += add_items(item_list)
                    # Item change list
                    else:
                        for item in line.split(","):
                            # item_data = get_item(item)
                            md += f"1. {item.strip()}\n"
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
