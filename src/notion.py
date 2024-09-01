from container import Container
from config import Config
import re
import notion_client
import socket
import logging

class Notion:
    def __init__(self) -> None:
        self.notion = notion_client.Client(auth=Config().get("NOTION_AUTH_TOKEN"), log_level=logging.DEBUG)

    def find_notion_page_id(self, container_name: str, server_name: str) -> str:
        query = self.notion.databases.query(
            **{
                "database_id": Config().get("NOTION_DATABASE_ID"),
                "filter": {
                    "and": [
                        {"property": "Container Name", "title": {"equals": container_name}},
                        {"property": "Server Name", "rich_text": {"equals": server_name}},
                    ]
                }
            }
        )
        if query["results"]:
            return query["results"][0]["id"]
        return None


    def update_notion_database(self, container_data: list) -> None:
        for container in container_data:
            # Den Image-Namen und Tag extrahieren (falls vorhanden)
            match = re.match(r"([^:]+)(?::([^/]+))?", container["image"])
            if match:
                repo = match.group(1)
                current_tag = match.group(2) if match.group(2) else "latest"
            else:
                repo = container["image"]
                current_tag = "latest"

            local_digest = Container().get_local_image_digest(container["image"])
            remote_digest, remote_last_updated = Container().get_remote_image_info(repo, current_tag)
            latest_digest, latest_last_updated = Container().get_remote_image_info(repo, "latest")

            needs_update = local_digest != remote_digest if local_digest and remote_digest else True
            newer_version_available = (
                    current_tag != "latest" and remote_last_updated < latest_last_updated
            ) if remote_last_updated and latest_last_updated else False

            # Notion-Seite suchen oder erstellen
            page_id = self.find_notion_page_id(container["name"], socket.gethostname())

            properties = {
                "Container Name": {"title": [{"text": {"content": container["name"]}}]},
                "Server Name": {"rich_text": [{"text": {"content": socket.gethostname()}}]},
                "Image": {"rich_text": [{"text": {"content": container["image"]}}]},
                "Current Tag": {"rich_text": [{"text": {"content": current_tag}}]},
                "Local Digest": {"rich_text": [{"text": {"content": local_digest or 'unknown'}}]},
                "Remote Digest": {"rich_text": [{"text": {"content": remote_digest or 'unknown'}}]},
                "Latest Digest": {"rich_text": [{"text": {"content": latest_digest or 'unknown'}}]},
                "Needs Update": {"checkbox": needs_update},
                "Newer Version Available": {"checkbox": newer_version_available},
            }


            if page_id:
                # Vorhandene Seite aktualisieren
                self.notion.pages.update(page_id=page_id, properties=properties)
            else:
                # Neue Seite erstellen
                self.notion.pages.create(parent={"database_id": Config().get("NOTION_DATABASE_ID")}, properties=properties)
