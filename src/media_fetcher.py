import os
import re
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from util.logger import Logger


def request(url: str, timeout: int, session: requests.Session, logger: Logger) -> requests.models.Response:
    """
    Fetch the HTML content of the URL using a session with retries.

    :param url: The URL to fetch the HTML content from.
    :param timeout: The timeout (in seconds) for the request.
    :param session: The session to use for the request.
    :param logger: The logger to log the request.
    :return: The response from the URL.
    """

    while True:
        try:
            response = session.get(url, timeout=timeout)
            logger.log(logging.INFO, f"Fetched the URL: {url}.")
            return response
        except requests.exceptions.RequestException as e:
            logger.log(logging.ERROR, f"Failed to fetch the URL: {url}. {e}")
            time.sleep(timeout)  # Wait before retrying


def save_sprite(url: str, view: str, pokemon: str, timeout: int, session: requests.Session, logger: Logger) -> None:
    """
    Fetch and save a single sprite image.

    :param url: The URL of the sprite image.
    :param view: The view name (used as file name).
    :param pokemon: The Pokémon name (used as directory name).
    :param timeout: The timeout for the request.
    :param session: The session to use for the request.
    :param logger: The logger to log the actions.
    """

    # Fetch the sprite image
    response = request(url, timeout, session, logger)

    # Create the directory for the sprite image if it doesn't exist
    directory = os.path.join("..", "docs", "assets", "sprites", pokemon)
    os.makedirs(directory, exist_ok=True)

    # Save the sprite image
    file_path = os.path.join(directory, f"{view}.gif")
    with open(file_path, "wb") as file:
        file.write(response.content)

    logger.log(logging.INFO, f"Saved the sprite: {file_path}.")


def fetch_sprites(url: str, threads: int, timeout: int, session: requests.Session, logger: Logger):
    """
    Fetch the sprites from the given URL using a thread pool.

    :param url: The URL to fetch the sprites from.
    :param threads: Maximum number of threads to use concurrently.
    :param timeout: The timeout for each request.
    :param session: The session to use for the requests.
    :param logger: The logger to log the actions.
    """

    # Fetch the HTML content of the URL
    response = request(url, timeout, session, logger)

    # Parse the HTML content for the sprites
    soup = BeautifulSoup(response.text, "html.parser")
    sprites = soup.find_all("img")

    # Use a ThreadPoolExecutor to fetch and save sprites concurrently
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for sprite in sprites:
            src = sprite.get("src", "")
            # Define the pattern to match the sprite URL
            pattern = r"https:\/\/projectpokemon\.org\/images\/sprites-models\/([a-z\-]+)\/([a-z\-]+)\.gif"
            match = re.match(pattern, src)
            if not match:
                continue

            view, pokemon = match.groups()
            if pokemon.endswith("-f"):
                pokemon = pokemon[:-2]
                view += "-f"
            futures.append(executor.submit(save_sprite, src, view, pokemon, timeout, session, logger))
        # Optionally, wait for all submitted tasks to complete
        for future in futures:
            # Calling result() will re-raise any exceptions from the worker threads
            future.result()


def main():
    # Load environment variables and logger configuration
    load_dotenv()
    THREADS = int(os.getenv("THREADS", 5))
    TIMEOUT = int(os.getenv("TIMEOUT", 10))
    LOG = os.getenv("LOG")
    LOG_PATH = os.getenv("LOG_PATH")

    logger = Logger("Media Fetcher", os.path.join(LOG_PATH, "media_fetcher.log"), LOG)

    # Create a session and configure it with a retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # Total number of retries allowed
        backoff_factor=1,  # A delay factor between retries (e.g., 1, 2, 4, 8 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP statuses to force a retry
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # Methods to retry
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Fetch the sprites for each generation
    generations = 6
    for i in range(1, generations + 1):
        url = f"https://projectpokemon.org/home/docs/spriteindex_148/3d-models-generation-{i}-pokémon-r{89 + i}"
        logger.log(logging.INFO, f"Processing generation {i} from URL: {url}")
        fetch_sprites(url, THREADS, TIMEOUT, session, logger)


if __name__ == "__main__":
    main()
