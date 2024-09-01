from container import Container
from notion import Notion

def main():
    containers = Container().get_running_containers()
    Notion().update_notion_database(containers)

if __name__ == "__main__":
    main()