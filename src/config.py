import os
import logging

class Config:
    def __init__(self) -> None:
        self.config = {}

    def get(self, key: str) -> str:
        value = os.getenv(key)
        if value is None:
            logging.error(f"Environment variable {key} not set")
            raise KeyError(f"Environment variable {key} not set")
        return value
