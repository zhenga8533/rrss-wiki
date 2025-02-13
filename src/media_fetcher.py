import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util.file import load
from util.format import fix_pokemon_form, verify_pokemon_form
from util.logger import Logger


def fetch_url(url: str, timeout: int, session: requests.Session, logger: Logger) -> requests.models.Response:
    """
    Fetch the content of the given URL using the provided session.
    Assumes that URLs are valid, so only one request attempt is made.

    :param url: URL to fetch.
    :param timeout: Request timeout in seconds.
    :param session: The requests session.
    :param logger: Logger instance.
    :return: Response from the URL.
    """

    while True:
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code != 200:
                logger.log(logging.ERROR, f"Failed to fetch URL: {url}. Status code: {response.status_code}")
                return None

            logger.log(logging.INFO, f"Fetched URL: {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.log(logging.ERROR, f"Error fetching URL: {url}. Exception: {e}")


def save_media(
    url: str,
    view: str,
    directory: str,
    timeout: int,
    session: requests.Session,
    logger: Logger,
    extension: str = None,
) -> None:
    """
    Fetch and save a sprite image.

    :param url: URL of the sprite image.
    :param view: View name used in the file name.
    :param pokemon: Pokémon (or form) name used as the directory name.
    :param timeout: Request timeout in seconds.
    :param session: The requests session.
    :param logger: Logger instance.
    :param extension: Explicit extension to use for the file.
    :return: None
    """

    response = fetch_url(url, timeout, session, logger)
    if response is None:
        return
    os.makedirs(directory, exist_ok=True)

    if extension is None:
        # Attempt to extract extension from the URL; default to .gif if not found.
        _, ext = os.path.splitext(url)
        extension = ext if ext else ".gif"

    file_path = os.path.join(directory, view + extension)
    try:
        file_path = file_path.replace("\\", "/")
        if not os.path.exists(file_path):
            with open(file_path, "wb") as file:
                file.write(response.content)
            logger.log(logging.INFO, f"Saved sprite: {file_path}")
        else:
            logger.log(logging.WARNING, f"Skipping existing sprite: {file_path}")
    except Exception as e:
        logger.log(logging.ERROR, f"Error saving sprite at {file_path}: {e}")
        raise


def fetch_sprites(url: str, threads: int, timeout: int, session: requests.Session, logger: Logger) -> None:
    """
    Fetch sprites from the specified URL using a thread pool.

    :param url: URL to fetch the sprite page from.
    :param threads: Maximum number of concurrent threads.
    :param timeout: Request timeout in seconds.
    :param session: The requests session.
    :param logger: Logger instance.
    :return: None
    """

    response = fetch_url(url, timeout, session, logger)
    if response is None:
        return

    soup = BeautifulSoup(response.text, "html.parser")
    sprites = soup.find_all("img")
    pattern = r"https:\/\/projectpokemon\.org\/images(?:\/[a-z\-]+)?\/([a-z\-]+)\/([a-z_0-9\-]+)\.gif"

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for sprite in sprites:
            # Extract view and Pokémon from the URL using the pattern
            src = sprite.get("src", "")
            match = re.match(pattern, src)
            if not match:
                logger.log(logging.WARNING, f"Skipping invalid sprite URL: {src}")
                continue
            view, pokemon = match.groups()

            # Fix view format
            view = view.replace("sprite", "front")
            view = view.replace("normal-", "")
            if "shiny-" in view:
                view = view.replace("shiny-", "")
                view += "_shiny"
            if pokemon.endswith("-f"):
                pokemon = pokemon[:-2]
                view += "_female"

            # Fix certain Pokemon forms
            if "pikachu" in pokemon:
                if "cap" in pokemon:
                    continue
                pokemon = pokemon.replace("popstar", "pop-star")
                pokemon = pokemon.replace("rockstar", "rock-star")
            if "nidoran" in pokemon:
                pokemon = pokemon.replace("_m", "-m")
                pokemon = pokemon.replace("_f", "-f")
            if "unown" in pokemon:
                if "interrogation" in pokemon:
                    pokemon = pokemon.replace("interrogation", "question")
                elif "-" in pokemon:
                    pokemon, extension = pokemon.split("-")
                    pokemon = f"{pokemon}-{extension[0]}"
            if pokemon == "basculin-blue":
                pokemon = "basculin-blue-striped"
            if pokemon == "xerneas":
                pokemon = "xerneas-neutral"
            if pokemon == "xerneas-active":
                pokemon = "xerneas"
            if "genesect" in pokemon:
                pokemon = pokemon.replace("water", "douse")
                pokemon = pokemon.replace("fire", "burn")
                pokemon = pokemon.replace("electric", "shock")
                pokemon = pokemon.replace("ice", "chill")
            if "scatterbug" in pokemon or "spewpa" in pokemon or "vivillon" in pokemon:
                pokemon = pokemon.replace("highplains", "high-plains")
                pokemon = pokemon.replace("pokeball", "poke-ball")
                pokemon = pokemon.replace("savannah", "savanna")
            if "furfrou" in pokemon:
                pokemon = pokemon.replace("lareine", "la-reine")
            pokemon = fix_pokemon_form(pokemon)

            # Mega evolutions
            pokemon = pokemon.replace("megax", "mega-x")
            pokemon = pokemon.replace("megay", "mega-y")

            # Gen 6 mismatch with higher generations
            pokemon = pokemon.replace("_g6", "")
            if pokemon == "glameow":
                continue

            # Check if the form is valid before saving the sprite
            if not verify_pokemon_form(pokemon, logger):
                continue
            directory = "../docs/assets/sprites/" + pokemon
            futures.append(executor.submit(save_media, src, view, directory, timeout, session, logger))

        # Wait for all tasks to complete, propagating any exceptions
        for future in futures:
            future.result()


def fetch_media(pokemon: dict, pokemon_path: str, session: requests.Session, logger: Logger) -> None:
    """
    Fetch and save media (sprites and cries) for a single Pokémon.

    :param pokemon: Dictionary containing Pokémon details.
    :param pokemon_path: Directory where Pokémon JSON files are stored.
    :param session: The requests session.
    :param logger: Logger instance.
    :return: None
    """

    name = pokemon["name"]
    data_path = os.path.join(pokemon_path, f"{name}.json")
    data = json.loads(load(data_path, logger))
    forms = data.get("forms", [])

    for form in forms:
        # Process only valid forms (or the default form)
        if form != name and not verify_pokemon_form(form, logger):
            continue

        form_path = os.path.join(pokemon_path, f"{form}.json")
        form_data_content = load(form_path, logger)
        form_data = json.loads(form_data_content) if form_data_content else data

        sprites = form_data.get("sprites", {})
        official_artwork = sprites.get("other", {}).get("official-artwork", {})
        official = official_artwork.get("front_default")
        official_shiny = official_artwork.get("front_shiny")
        sprite_data = {"official": official, "official_shiny": official_shiny}

        # Generation 6, ORAS sprites
        oras = sprites["versions"]["generation-vi"]["omegaruby-alphasapphire"]
        for key, sprite in oras.items():
            sprite_name = key.replace("_default", "")
            if sprite:
                sprite_data[sprite_name] = sprite

        # Save all sprite images using save_media
        for key, sprite_url in sprite_data.items():
            if not sprite_url:
                continue
            logger.log(logging.INFO, f"Fetching sprite for {form} from {sprite_url}")
            directory = "../docs/assets/sprites/" + form
            save_media(sprite_url, key, directory, 10, session, logger, extension=".png")

        # Save cries (audio) using the original approach
        cry_latest = form_data.get("cry_latest")
        cry_legacy = form_data.get("cry_legacy")
        cries = {
            "latest": cry_latest or cry_legacy,
            "legacy": cry_legacy or cry_latest,
        }
        for key, cry_url in cries.items():
            if cry_url is None:
                continue
            logger.log(logging.INFO, f"Fetching cry for {form} from {cry_url}")
            directory = "../docs/assets/cries/" + form
            save_media(cry_url, key, directory, 10, session, logger)


def main():
    """
    Main function to fetch Pokémon media (sprites and cries) using the PokéAPI and Project Pokémon.

    :return: None
    """

    # Load environment variables and configure logging
    load_dotenv()
    THREADS = int(os.getenv("THREADS", 5))
    TIMEOUT = int(os.getenv("TIMEOUT", 10))
    POKEMON_INPUT_PATH = os.getenv("POKEMON_INPUT_PATH", "./pokemon_data/")
    LOG = os.getenv("LOG", "INFO")
    LOG_PATH = os.getenv("LOG_PATH", "./logs/")

    logger = Logger("Media Fetcher", os.path.join(LOG_PATH, "media_fetcher.log"), LOG)

    # Create a session with a retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # Total number of retries allowed
        backoff_factor=1,  # Delay factor between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Fetch Project Pokémon sprites for specified generations concurrently
    generations = 6
    for i in range(1, generations + 1):
        url = f"https://projectpokemon.org/home/docs/spriteindex_148/3d-models-generation-{i}-pokémon-r{89 + i}"
        logger.log(logging.INFO, f"Processing generation {i} from URL: {url}")
        fetch_sprites(url, THREADS, TIMEOUT, session, logger)

    # Fetch the list of Pokémon from the API
    pokedex_url = "https://pokeapi.co/api/v2/pokemon/?offset=0&limit=721"
    pokedex_response = fetch_url(pokedex_url, TIMEOUT, session, logger)
    if pokedex_response is None:
        return

    pokedex = pokedex_response.json().get("results", [])
    logger.log(logging.INFO, f"Fetched pokedex with {len(pokedex)} Pokémon")

    # Process the pokedex sequentially using threads that are created and joined one at a time
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for pokemon in pokedex:
            futures.append(executor.submit(fetch_media, pokemon, POKEMON_INPUT_PATH, session, logger))

        # Wait for all tasks to complete, propagating any exceptions
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
