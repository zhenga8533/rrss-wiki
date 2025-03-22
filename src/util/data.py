import json
import logging
import os

from util.file import download_file, load, save
from util.format import format_id


class Data:
    def __init__(self, input_path: str, logger: str):
        """
        Initializes the Data class with a path to the input files and a logger.

        :param input_path: The path to the directory containing the JSON files.
        :param logger: A logger instance for logging messages.
        """

        self.cache = {}
        self.input_path = input_path
        self.logger = logger

    def get_data(self, name: str) -> dict:
        """
        Returns the data for a given name. If the data is not found in the cache, it loads it from a JSON file.

        :param name: The name of the item or entity.
        :return: A dictionary containing the data for the item or entity, or None if not found.
        """

        data_id = format_id(name)
        if data_id in self.cache:
            return self.cache[data_id]
        else:
            file_path = self.input_path + data_id + ".json"
            if os.path.exists(file_path):
                data = json.loads(load(file_path, self.logger))
                self.cache[data_id] = data
                return data
            else:
                self.logger.log(logging.ERROR, f"Data {data_id} not found")
                return None

    def get_image(self, name: str) -> str:
        """
        Returns the image path for a given name. If the image does not exist, it downloads it.

        :param name: The name of the item
        :return: The path to the image file
        """

        name = name.strip()
        data = self.get_data(name)
        if data is None:
            data = self.get_data(name.split(" ")[0])
        if data is None:
            self.logger.log(logging.ERROR, f"Image data for {name} not found")
            return name

        item_path = f"../docs/assets/items/{format_id(name, symbol="_")}.png"
        if not os.path.exists(item_path):
            download_file(item_path, data["sprite"], self.logger)

        return f'![{name}]({item_path.replace("docs", "..")} "{name}")'

    def get_tooltip(self, name: str, game: str) -> str:
        """
        Returns a tooltip for the given name and game.

        :param name: The name of the item or entity.
        :param game: The game context (e.g., "platinum" or "omega-ruby-alpha-sapphire").
        "return: A string containing the HTML for the tooltip."
        """

        name = name.strip()
        data = self.get_data(name)
        if data is None:
            data = self.get_data(name.split(" ")[0])
        if data is None:
            self.logger.log(logging.ERROR, f"Tooltip data for {name} not found")
            return name

        entries = data["flavor_text_entries"]
        flavor_text = entries[game] if game in entries else data["effect"]
        flavor_text = flavor_text.replace("\n", " ")

        tooltip = f'<span class="tooltip" title="{flavor_text}">{name}</span>'
        return tooltip

    def save_data(self, name: str, data: dict) -> None:
        """
        Saves the given data to a JSON file and updates the cache.

        :param name: The name of the item or entity.
        :param data: The data to be saved as a dictionary.
        """

        data_id = format_id(name)
        self.cache[data_id] = data

        file_path = self.input_path + data_id + ".json"
        save(file_path, json.dumps(data, indent=4), self.logger)
