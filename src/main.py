from container import Container
from notion import Notion
from config import Config
import time

def main():

    # Tests
    # Container().get_remote_image_info(image_name="docker.io/vaultwarden/server:latest")
    # Container().get_local_image_digest(image_name="docker.io/vaultwarden/server:latest")
    sync_interval = Config().get("SYNC_INTERVAL")

    # Ensure sync_interval is an integer
    if not isinstance(sync_interval, int):
        raise TypeError(f"Expected SYNC_INTERVAL to be of type int, got {type(sync_interval).__name__} instead")

    print(f"Sync interval set to {sync_interval} seconds")

    while True:
        # Worker
        print("Script is starting...")
        containers = Container().get_running_containers()
        print(containers)
        print("Container.py executed successfully")
        print("Starting notion.py...")
        Notion().update_notion_database(containers)

        # Calculate minutes and seconds
        minutes, seconds = divmod(sync_interval, 60)
        if minutes > 0:
            print(f"Update completed. Waiting for the next sync in {minutes} minute{'s' if minutes > 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}...")
        else:
            print(f"Update completed. Waiting for the next sync in {seconds} second{'s' if seconds != 1 else ''}...")

        time.sleep(sync_interval)


if __name__ == "__main__":
    main()