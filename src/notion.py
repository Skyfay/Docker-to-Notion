from container import Container
from config import Config
import re
import notion_client
import socket
import logging

class Notion:
    def __init__(self) -> None:
        self.notion = notion_client.Client(auth=Config().get("NOTION_AUTH_TOKEN")) # log_level=logging.DEBUG

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

            # Bis hier sollte der code in Ordnung sein. Nun folgt die neue Logik mit vergleich zwischen local und
            # remote digest, sowie local und remote version. Wenn die unterschiedlich sind, dann ist es ein update.
            # Notion soll dann auch anzeigen, was die remote version ist jedoch nur wenn es ein Update gibt.

            local_digest, local_tag, local_version = Container().get_local_image_digest(container["image"])
            remote_digest, remote_version = Container().get_remote_image_info(container["image"])
            remote_version_latest = Container().get_remote_image_latest(container["image"])

            # Vergleich der Digests und Versionen
            needs_update = local_digest != remote_digest if local_digest and remote_digest else True
            newer_version_available = (
                current_tag != "latest" and remote_version_latest != local_version
            ) if remote_version and local_version else False

            # Notion-Seite suchen oder erstellen
            page_id = self.find_notion_page_id(container["name"], socket.gethostname())

            # Bestimme den Wert für "New Version"
            if newer_version_available:
                new_version = remote_version_latest
            elif needs_update:
                new_version = remote_version
            else:
                new_version = None

            properties = {
                "Container Name": {"title": [{"text": {"content": container["name"] or "unknown"}}]},
                "Server Name": {"rich_text": [{"text": {"content": socket.gethostname() or "unknown"}}]},
                "Image": {"rich_text": [{"text": {"content": container["image"] or "unknown"}}]},
                "Current Tag": {"rich_text": [{"text": {"content": current_tag}}]},
                "Current Version": {"rich_text": [{"text": {"content": local_version or "unknown"}}]},
                "Local Digest": {"rich_text": [{"text": {"content": local_digest or 'unknown'}}]},
                "Remote Digest": {"rich_text": [{"text": {"content": remote_digest or 'unknown'}}]},
                "Needs Update": {"checkbox": needs_update},
                "Newer Tag Available": {"checkbox": newer_version_available},
            }

            # Nur wenn ein Update benötigt wird, die Remote Version hinzufügen
            if new_version:
                properties["New Version"] = {"rich_text": [{"text": {"content": new_version or 'unknown'}}]}

            if page_id:
                # Vorhandene Seite aktualisieren
                self.notion.pages.update(page_id=page_id, properties=properties)
            else:
                # Neue Seite erstellen
                self.notion.pages.create(parent={"database_id": Config().get("NOTION_DATABASE_ID")}, properties=properties)
