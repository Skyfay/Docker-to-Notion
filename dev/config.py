import os
import logging

class Config:
    def __init__(self) -> None:
        self.config = {}

        self.load(os.path.join(os.path.dirname(__file__), "..", ".env"))
    def load(self, path: str) -> None:
        try:
            with open(path, "r") as f:
                for line in f:
                    key, value = line.strip().split("=")
                    self.config[key] = value
        except FileNotFoundError:
            logging.error(f"File {path} not found")
            raise

    def get(self, key: str) -> str:
        return self.config[key]
