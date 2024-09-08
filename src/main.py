from container import Container
from notion import Notion
import time

def main():

    # Tests
    # Container().get_remote_image_info(image_name="docker.io/vaultwarden/server:latest")
    # Container().get_local_image_digest(image_name="docker.io/vaultwarden/server:latest")
    while True:
    # Worker
        print("Script is starting...")
        containers = Container().get_running_containers()
        print(containers)
        print("Container.py executed successfully")
        print("Starting notion.py...")
        Notion().update_notion_database(containers)
        print("Update completed. Waiting for the next sync...")
        time.sleep(300)


if __name__ == "__main__":
    main()