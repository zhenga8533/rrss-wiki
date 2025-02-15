import json
import logging
import os

from util.file import load, save
from util.format import format_id


class Data:
    def __init__(self, input_path: str, logger: str):
        self.cache = {}
        self.input_path = input_path
        self.logger = logger

    def get_data(self, name: str) -> dict:
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

    def get_tooltip(self, name: str, game: str) -> str:
        name = name.strip()
        data = self.get_data(name)
        if data is None:
            data = self.get_data(name.split(" ")[0])
        flavor_text = data["flavor_text_entries"][game].replace("\n", " ")

        tooltip = f'<span class="tooltip" title="{flavor_text}">{name}</span>'
        return tooltip

    def save_data(self, name: str, data: dict) -> None:
        data_id = format_id(name)
        self.cache[data_id] = data

        file_path = self.input_path + data_id + ".json"
        save(file_path, json.dumps(data, indent=4), self.logger)
