import os
import logging

class Config:
    def __init__(self) -> None:
        self.config = {}

        self.load(os.path.join(os.path.dirname(__file__), "..", ".env"))
    
    
    """
    load the config from the .env file
    
    :param path: path to the .env file
    :type path: str
    :return: None
    """
    def load(self, path: str) -> None:
        try:
            with open(path, "r") as f:
                for line in f:
                    key, value = line.strip().split("=")
                    self.config[key] = value
        except FileNotFoundError:
            logging.error(f"File {path} not found")
            raise

    """
    get a config value
    
    :param key: key of the config value
    :type key: str
    :return: config as string
    """
    def get(self, key: str) -> str:
        return self.config[key]
