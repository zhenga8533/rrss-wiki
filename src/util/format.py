import json
import logging
import os
import re
import string

from util.file import load, verify_asset_path
from util.logger import Logger


def check_empty(line: str) -> bool:
    """
    Check if a line is empty.

    :param line: The line to check.
    :return: True if the line is empty, False otherwise.
    """

    return len(line) == 0 or line.startswith("o-") or line.startswith("===") or len(line.strip("| ")) == 0


def find_pokemon_sprite(pokemon: str, view: str, logger: Logger) -> str:
    """
    Find the sprite of a Pokémon.

    :param pokemon: Pokémon to find the sprite.
    :param view: View of the sprite.
    :param logger: Logger to log the verification.
    :return: The sprite of the Pokémon.
    """

    # Load Pokemon data
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH")
    pokemon_id = format_id(pokemon)

    file_path = POKEMON_INPUT_PATH + pokemon_id + ".json"
    if not os.path.exists(file_path):
        file_path = file_path.replace(pokemon_id, pokemon_id.rsplit("-", 1)[0])
        if not os.path.exists(file_path):
            return "?"
    pokemon_data = json.loads(load(file_path, logger))

    pokemon_text = pokemon_data["flavor_text_entries"].get("alpha-sapphire", pokemon).replace("\n", " ")
    sprite = f"../assets/sprites/{pokemon_id}/{view}"

    # Return the sprite that exists
    return (
        f'![{pokemon}]({sprite}.gif "{pokemon}: {pokemon_text}")'
        if verify_asset_path(sprite + ".gif", logger)
        else (
            f'![{pokemon}]({sprite}.png "{pokemon}: {pokemon_text}")'
            if verify_asset_path(sprite + ".png", logger)
            else "?"
        )
    )


def find_trainer_sprite(trainer: str, view: str, logger: Logger = None) -> str:
    """
    Find the sprite of a trainer.

    :param trainer: Trainer to find the sprite.
    :param view: View of the sprite.
    :param logger: Logger to log the verification.
    :return: The sprite of the trainer.
    """

    words = trainer.split()
    n = len(words)
    subsets = []

    # Iterate through all non-empty subsets
    for i in range(1, 1 << n):
        subset = []
        for j in range(n):
            # Check if the j-th element is in the subset
            if i & (1 << j):
                subset.append(words[j])
        subsets.append(" ".join(subset))
    subsets.sort(key=len, reverse=True)

    # Check if the sprite exists for any subset
    for subset in subsets:
        sprite = f"../assets/{view}/{format_id(subset, symbol='_')}"
        if verify_asset_path(sprite + ".png", logger):
            return f'![{trainer}]({sprite}.png "{trainer}")'

    # Check if the sprite exists for the full name
    if view != "important_trainers":
        return find_trainer_sprite(trainer, "important_trainers", logger)

    logger.log(logging.ERROR, f"Sprite not found for {trainer}")
    return f'![{trainer}](../assets/{view}/{format_id(trainer, symbol="_")}.png "{trainer}")'


def fix_pokemon_form(form: str) -> str:
    """
    Fix the id of a Pokemon with multiple forms.

    :param form: Pokémon form to be fixed.
    :return: Fixed form id.
    """

    fix_map = {
        "deoxys": "deoxys-normal",
        "wormadam": "wormadam-plant",
        "giratina": "giratina-altered",
        "shaymin": "shaymin-land",
        "darmanitan": "darmanitan-standard",
        "basculin": "basculin-red-striped",
        "pumpkaboo": "pumpkaboo-average",
        "gourgeist": "gourgeist-average",
        "tornadus": "tornadus-incarnate",
        "thundurus": "thundurus-incarnate",
        "landorus": "landorus-incarnate",
        "keldeo": "keldeo-ordinary",
        "meloetta": "meloetta-aria",
        "aegislash": "aegislash-shield",
        "meowstic": "meowstic-male",
        "zygarde": "zygarde-50",
    }

    if form in fix_map:
        return fix_map[form]
    return form


def format_id(id: str, symbol: str = "-") -> str:
    """
    Format the ID of any string.

    :param id: ID to be formatted.
    :return: Formatted ID.
    """

    id = id.replace("é", "e")
    id = re.sub(r"[^a-zA-Z0-9é\s-]", "", id)
    id = re.sub(r"\s+", " ", id).strip()
    id = id.lower().replace(" ", symbol)
    return fix_pokemon_form(id)


def format_stat(stat: str) -> str:
    """
    Format the name of a stat.

    :param stat: Stat to be formatted.
    :return: Formatted stat.
    """

    stat = format_id(stat)
    formats = [
        ("health", "HP"),
        ("hp", "HP"),
        ("attack", "Atk"),
        ("defense", "Def"),
        ("special", "Sp."),
        ("speed", "Spd"),
    ]

    for old, new in formats:
        stat = stat.replace(old, new)

    return stat


def revert_id(id: str, symbol: str = "-") -> str:
    """
    Revert the ID of a Pokémon.

    :param id: ID to be reverted.
    :return: Reverted ID.
    """

    return string.capwords(id.replace(symbol, " "))


def verify_pokemon_form(id: str, logger: Logger) -> bool:
    """
    Verify if a Pokemon form is valid.

    :param id: The ID of the Pokemon.
    :param logger: The logger to use.
    :return: True if the form is valid, False otherwise.
    """

    invalid_forms = [
        "alola",
        "galar",
        "hisui",
        "paldea",
        "-cap",
        "-starter",
        "-totem",
        "-gmax",
        "white-striped",
        "dialga-origin",
        "palkia-origin",
        "scatterbug-",
        "spewpa-",
        "battle-bond",
    ]

    # Validate if the Pokemon has a form
    for form in invalid_forms:
        if form in id:
            logger.log(logging.DEBUG, f"Invalid form: {id}")
            return False

    logger.log(logging.DEBUG, f"Valid form: {id}")
    return True
