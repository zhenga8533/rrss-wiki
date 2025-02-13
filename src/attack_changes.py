import logging
import os
import re

from dotenv import load_dotenv

from util.file import load, save
from util.format import check_empty
from util.logger import Logger


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
            md += f"### {line}\n\n"
            md += "| Attribute | Old | New |\n"
            md += "| --------- | --- | --- |\n"

            i += 2
            while i < n and not check_empty(line := lines[i]):
                attribute, change = re.split(r"\s{2,}", line, 1)
                old, new = change.split(" >> ") if " >> " in change else ("None", change)
                md += f"| {attribute} | {old} | {new} |\n"
                i += 1
            md += "\n"
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
