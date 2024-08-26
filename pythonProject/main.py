import docker
import requests
from notion_client import Client
import re

# Konfiguration
SERVER_NAME = "Skyv24"  # Servername hier eintragen

# Docker-Client initialisieren
client = docker.from_env()

# Notion-Client initialisieren
notion = Client(auth="xxxxxx")

# Notion-Datenbank-ID
DATABASE_ID = "041bf43f02fc48c5adf3b17a42f94fe6"


def get_running_containers():
    containers = client.containers.list()
    container_data = []
    for container in containers:
        container_info = {
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else "N/A"
        }
        container_data.append(container_info)
    return container_data


def get_local_image_digest(image_name):
    try:
        image = client.images.get(image_name)
        return image.attrs['RepoDigests'][0].split('@')[1]
    except Exception as e:
        print(f"Error fetching local digest for {image_name}: {e}")
        return None


def get_remote_image_info(repo, tag="latest"):
    url = f"https://registry.hub.docker.com/v2/repositories/{repo}/tags/{tag}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        digest = data['images'][0]['digest']
        last_updated = data['last_updated']
        return digest, last_updated
    else:
        print(f"Error fetching info from Docker Hub for {repo}:{tag} - Status code: {response.status_code}")
        return None, None


def find_notion_page_id(container_name, server_name):
    query = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
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


def update_notion_database(container_data):
    for container in container_data:
        # Den Image-Namen und Tag extrahieren (falls vorhanden)
        match = re.match(r"([^:]+)(?::([^/]+))?", container["image"])
        if match:
            repo = match.group(1)
            current_tag = match.group(2) if match.group(2) else "latest"
        else:
            repo = container["image"]
            current_tag = "latest"

        local_digest = get_local_image_digest(container["image"])
        remote_digest, remote_last_updated = get_remote_image_info(repo, current_tag)
        latest_digest, latest_last_updated = get_remote_image_info(repo, "latest")

        needs_update = local_digest != remote_digest if local_digest and remote_digest else True
        newer_version_available = (
                current_tag != "latest" and remote_last_updated < latest_last_updated
        ) if remote_last_updated and latest_last_updated else False

        # Notion-Seite suchen oder erstellen
        page_id = find_notion_page_id(container["name"], SERVER_NAME)

        properties = {
            "Container Name": {"title": [{"text": {"content": container["name"]}}]},
            "Server Name": {"rich_text": [{"text": {"content": SERVER_NAME}}]},
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
            notion.pages.update(page_id=page_id, properties=properties)
        else:
            # Neue Seite erstellen
            notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)


def main():
    containers = get_running_containers()
    update_notion_database(containers)


if __name__ == "__main__":
    main()
