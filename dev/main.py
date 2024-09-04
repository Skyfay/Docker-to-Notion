from container import Container
from notion import Notion

def main():

    # Tests
    # Container().get_remote_image_info(image_name="docker.io/vaultwarden/server:latest")
    # Container().get_local_image_digest(image_name="docker.io/vaultwarden/server:latest")

    # Worker
    containers = Container().get_running_containers()
    Notion().update_notion_database(containers)


if __name__ == "__main__":
    main()