import docker
import requests

class Container:
    def __init__(self) -> None:
        self.docker = docker.from_env()

    def get_running_containers(self) -> list:
        containers = self.docker.containers.list()
        container_data = []
        for container in containers:
            container_info = {
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "N/A"
            }
            container_data.append(container_info)
        return container_data


    def get_local_image_digest(self,image_name: str) -> str:
        try:
            image = self.docker.images.get(image_name)
            return image.attrs['RepoDigests'][0].split('@')[1]
        except Exception as e:
            print(f"Error fetching local digest for {image_name}: {e}")
            return None


    def get_remote_image_info(self, repo: str, tag: str = "latest") -> tuple[str, str]:
        if len(repo.split("/")) == 1:
            repo = f"library/{repo}"

        response = requests.get(f"https://registry.hub.docker.com/v2/repositories/{repo}/tags/{tag}")

        if response.status_code == 200:
            data = response.json()
            digest = data['images'][0]['digest']
            last_updated = data['last_updated']
            return digest, last_updated
        else:
            print(f"Error fetching info from Docker Hub for {repo}:{tag} - Status code: {response.status_code}")
            return None, None
