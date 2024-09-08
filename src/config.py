import os
import logging
import json

class Config:
    def __init__(self) -> None:
        self.config = {}
    # works with docker-compose env
    def get(self, key: str) -> str:
        value = os.getenv(key)
        if value is None:
            logging.error(f"Environment variable {key} not set")
            raise KeyError(f"Environment variable {key} not set")

        if key == "EXCLUDED_IMAGES":
            # Parse JSON array
            return json.loads(value)

        if key == "SYNC_INTERVAL":
            # Parse the interval and ensure it is at least 300 seconds
            try:
                interval = int(value)
                return max(interval, 300)  # Minimum interval is 300 seconds
            except ValueError:
                logging.error(f"Invalid value for {key}: {value}")
                raise

        return value

#class Config:
#    def __init__(self) -> None:
#        self.config = {}
#        self.load(os.path.join(os.path.dirname(__file__), "..", ".env"))
#    def load(self, path: str) -> None:
#        try:
#            with open(path, "r") as f:
#                for line in f:
#                    key, value = line.strip().split("=")
#                    self.config[key] = value
#        except FileNotFoundError:
#            logging.error(f"File {path} not found")
#            raise
#    def get(self, key: str) -> str:
#        return self.config[key]
